import os
import logging
import base64
import uuid
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage
from unstructured.partition.pdf import partition_pdf

logger = logging.getLogger(__name__)

VECTORSTORE_PATH = Path(__file__).parent.parent / "vectorstore"
IMAGE_STORE_PATH = VECTORSTORE_PATH / "image_store"

TEXT_TABLE_SUMMARIZATION_PROMPT = """
You are an assistant tasked with summarizing tables and text. 
Give a concise summary of the table or text.
Respond only with the summary, no additional comment.
Do not start your message by saying "Here is a summary" or anything like that.
Just give the summary as it is.
Table or text chunk: {element}
"""

IMAGE_PROMPT_TEMPLATE = """
Describe the image in detail. For context, 
the image is from an educational document. Be specific about graphs, diagrams, 
charts, or any visual elements that would help students understand the content.
"""

BUILD_PROMPT_TEMPLATE = """
Answer the question based only on the following context, which can include text, tables, and images.
            
Context: {context_text}
            
Question: {user_question}
"""


class PDFProcessor:
    """Process and index PDFs from Google Classroom materials using advanced multi-modal RAG."""
    
    def __init__(self, classroom_tool):
        self.classroom_tool = classroom_tool
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.vectorstore = Chroma(
            persist_directory=str(VECTORSTORE_PATH),
            embedding_function=self.embeddings,
            collection_name="classroom_multimodal_rag"
        )

        IMAGE_STORE_PATH.mkdir(parents=True, exist_ok=True)
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        prompt_text = TEXT_TABLE_SUMMARIZATION_PROMPT
        prompt = ChatPromptTemplate.from_template(prompt_text)
        self.summarize_chain = {"element": lambda x: x} | prompt | self.llm | StrOutputParser()
        
        prompt_template = IMAGE_PROMPT_TEMPLATE
        messages = [
            (
                "user",
                [
                    {"type": "text", "text": prompt_template},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64,{image}"},
                    },
                ],
            )
        ]
        image_prompt = ChatPromptTemplate.from_messages(messages)
        self.image_summarization_chain = image_prompt | ChatOpenAI(model="gpt-4o-mini") | StrOutputParser()

    def _save_image_base64(self, image_b64: str) -> str:
        """Persist base64 image payload to disk and return a stable key."""
        digest = hashlib.sha256(image_b64.encode("utf-8")).hexdigest()[:16]
        image_key = f"img_{digest}_{uuid.uuid4().hex[:8]}"
        (IMAGE_STORE_PATH / f"{image_key}.b64").write_text(image_b64, encoding="utf-8")
        return image_key

    def _load_image_base64(self, image_key: str) -> Optional[str]:
        path = IMAGE_STORE_PATH / f"{image_key}.b64"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
    
    def extract_multimodal_content(self, pdf_bytes: bytes, temp_filename: str) -> Dict:
        """Extract text, tables, and images from PDF using unstructured."""
        temp_path = Path(VECTORSTORE_PATH) / "temp" / temp_filename
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            temp_path.write_bytes(pdf_bytes)
            
            chunks = partition_pdf(
                filename=str(temp_path),
                strategy="hi_res",
                infer_table_structure=True,
                extract_image_block_types=["Image"],
                extract_image_block_to_payload=True,
                chunking_strategy="by_title",
                max_characters=10000,
                combine_text_under_n_chars=2000,
                new_after_n_chars=6000,
            )
            
            images_b64 = []
            for chunk in chunks:
                if "CompositeElement" in str(type(chunk)):
                    if hasattr(chunk.metadata, 'orig_elements'):
                        chunk_els = chunk.metadata.orig_elements
                        for el in chunk_els:
                            if "Image" in str(type(el)):
                                if hasattr(el.metadata, 'image_base64') and el.metadata.image_base64:
                                    images_b64.append(el.metadata.image_base64)
            

            tables: List[Dict[str, str]] = []
            texts = []

            html_table_candidates = 0

            for chunk in chunks:
                # Capture tables
                html = None
                if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "text_as_html"):
                    html = getattr(chunk.metadata, "text_as_html", None)
                if html:
                    html_table_candidates += 1
                    chunk_text = chunk.text if hasattr(chunk, "text") else str(chunk)
                    tables.append({"html": str(html), "text": str(chunk_text)})
                elif "Table" in str(type(chunk)):
                    chunk_text = chunk.text if hasattr(chunk, "text") else str(chunk)
                    tables.append({"html": "", "text": str(chunk_text)})

                if "CompositeElement" in str(type(chunk)) and hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
                    for el in chunk.metadata.orig_elements or []:
                        if "Table" not in str(type(el)):
                            continue
                        el_html = None
                        if hasattr(el, "metadata") and hasattr(el.metadata, "text_as_html"):
                            el_html = getattr(el.metadata, "text_as_html", None)
                        if el_html:
                            html_table_candidates += 1
                        el_text = el.text if hasattr(el, "text") else str(el)
                        tables.append({"html": str(el_html or ""), "text": str(el_text)})

                if "CompositeElement" in str(type(chunk)):
                    texts.append(chunk)

            logger.info(
                "Unstructured table signals: html_candidates=%s, tables_collected=%s",
                html_table_candidates,
                len(tables),
            )

            return {"texts": texts, "tables": tables, "images": images_b64}
            
        except Exception as e:
            logger.error(f"Unstructured extraction failed: {e}")
            return {"texts": [], "tables": [], "images": []}
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def process_and_index_material(self, course_id: str, material: Dict) -> int:
        """Process and index PDFs with multi-modal content."""
        material_id = material['id']
        
        if self.vectorstore._collection.get(where={"material_id": material_id}, limit=1).get('ids'):
            return 0
        
        indexed = 0
        for attachment in material.get('materials', []):
            if 'driveFile' not in attachment:
                continue
                
            file = attachment['driveFile']['driveFile']
            if not file['title'].lower().endswith('.pdf'):
                continue
            
            logger.info(f"Processing PDF: {file['title']}")
            
            pdf_bytes = self.classroom_tool.download_drive_pdf(file['id'])
            if not pdf_bytes:
                continue
            
            content = self.extract_multimodal_content(pdf_bytes, file['title'])
            
            if not any([content["texts"], content["tables"], content["images"]]):
                logger.warning(f"No content extracted from {file['title']}")
                continue
            
            logger.info(f"Extracted {len(content['texts'])} texts, {len(content['tables'])} tables, {len(content['images'])} images")

            text_chunks = [t.text if hasattr(t, "text") else str(t) for t in content["texts"]]
            table_chunks = []
            for tbl in content["tables"]:
                if isinstance(tbl, dict):
                    table_chunks.append(str(tbl.get("html") or tbl.get("text") or ""))
                    continue
                table_chunks.append(
                    tbl.metadata.text_as_html
                    if hasattr(tbl, "metadata")
                    and hasattr(tbl.metadata, "text_as_html")
                    and tbl.metadata.text_as_html
                    else (tbl.text if hasattr(tbl, "text") else str(tbl))
                )
            
            image_summaries = []
            if content["images"]:
                try:
                    logger.info(f"Summarizing {len(content['images'])} images with vision model...")
                    image_summaries = self.image_summarization_chain.batch(
                        [{"image": img} for img in content["images"]],
                        {"max_concurrency": 2}
                    )
                    logger.info(f"Successfully summarized {len(image_summaries)} images")
                except Exception as e:
                    logger.error(f"Error summarizing images: {e}")
                    image_summaries = []
            
            base_metadata = {
                "course_id": course_id,
                "material_id": material_id,
                "material_title": material.get('title', ''),
                "file_id": file['id'],
                "filename": file['title'],
                "source": "google_classroom"
            }

            indexed += self._add_to_vectorstore(text_chunks, {**base_metadata, "type": "text"})
            indexed += self._add_to_vectorstore(table_chunks, {**base_metadata, "type": "table"})

            if content["images"] and image_summaries and len(image_summaries) == len(content["images"]):
                image_docs = []
                for i, (img_b64, img_summary) in enumerate(zip(content["images"], image_summaries)):
                    image_key = self._save_image_base64(img_b64)
                    image_docs.append(
                        Document(
                            page_content=img_summary,
                            metadata={**base_metadata, "type": "image", "chunk_index": i, "image_key": image_key}
                        )
                    )
                try:
                    self.vectorstore.add_documents(image_docs)
                    indexed += len(image_docs)
                except Exception as e:
                    logger.error(f"Error embedding image summaries: {e}")
            
            logger.info(f"Indexed {indexed} items from {file['title']}")
        
        return indexed
    
    def _add_to_vectorstore(self, items: List[str], base_metadata: Dict) -> int:
        """Add items directly to vectorstore."""
        docs: List[Document] = []
        for i, item in enumerate(items):
            if item and str(item).strip():
                docs.append(
                    Document(
                        page_content=str(item),
                        metadata={**base_metadata, "chunk_index": i}
                    )
                )

        if not docs:
            return 0
        try:
            self.vectorstore.add_documents(docs)
            return len(docs)
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            return 0
    
    def process_course_materials(self, course_id: str) -> Dict[str, int]:
        """Process all materials for a course."""
        materials = self.classroom_tool.list_coursework_materials(course_id)
        logger.info(f"Found {len(materials)} materials for course {course_id}")
        
        stats = {"materials_processed": len(materials), "pdfs_found": 0, "chunks_indexed": 0}
        
        for material in materials:
            pdf_count = sum(
                1 for m in material.get('materials', [])
                if 'driveFile' in m and m['driveFile']['driveFile']['title'].lower().endswith('.pdf')
            )
            stats["pdfs_found"] += pdf_count
            stats["chunks_indexed"] += self.process_and_index_material(course_id, material)
        
        logger.info(f"Course {course_id} complete: {stats}")
        return stats
    
    def get_retriever(self, k: int = 5, filter_dict: Optional[Dict] = None, use_mmr: bool = True):
        """Get a simple retriever from the vector store (no MultiVectorRetriever)."""
        search_kwargs = {"k": k}
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        
        search_type = "mmr" if use_mmr else "similarity"
        if use_mmr:
            search_kwargs["fetch_k"] = k * 3
        
        return self.vectorstore.as_retriever(search_type=search_type, search_kwargs=search_kwargs)
    
    def create_multimodal_chain(self):
        """Create a RAG chain that handles text, tables, and images."""
        retriever = self.get_retriever(k=5)
        
        def parse_docs(docs):
            """Split retrieved docs into image payloads and text docs."""
            b64_images: List[str] = []
            text_docs: List[Document] = []
            image_summaries: List[str] = []

            for doc in docs:
                if not isinstance(doc, Document):
                    continue

                doc_type = doc.metadata.get("type")
                if doc_type == "image":
                    image_summaries.append(doc.page_content)
                    image_key = doc.metadata.get("image_key")
                    if image_key:
                        img_b64 = self._load_image_base64(str(image_key))
                        if img_b64:
                            b64_images.append(img_b64)
                else:
                    text_docs.append(doc)

            for summary in image_summaries:
                text_docs.append(Document(page_content=f"Image description: {summary}", metadata={"type": "image_summary"}))

            return {"images": b64_images, "texts": text_docs}
        
        def build_prompt(kwargs):
            """Build multimodal prompt with text and images."""
            docs_by_type = kwargs["context"]
            user_question = kwargs["question"]
            
            context_text = ""
            if docs_by_type["texts"]:
                for text_element in docs_by_type["texts"]:
                    content = text_element.page_content if isinstance(text_element, Document) else str(text_element)
                    context_text += content + "\n\n"
            
            prompt_template = BUILD_PROMPT_TEMPLATE
            
            prompt_content = [{"type": "text", "text": prompt_template}]
            
            # add images to prompt
            if docs_by_type["images"]:
                for image in docs_by_type["images"]:
                    prompt_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                    })
            
            return ChatPromptTemplate.from_messages([HumanMessage(content=prompt_content)])
        
        chain = (
            {
                "context": retriever | RunnableLambda(parse_docs),
                "question": RunnablePassthrough(),
            }
            | RunnableLambda(build_prompt)
            | ChatOpenAI(model="gpt-4o-mini")
            | StrOutputParser()
        )
        
        return chain

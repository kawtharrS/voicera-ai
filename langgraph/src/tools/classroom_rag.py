import os
import logging
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
from ..prompts.classroom import (
    TEXT_TABLE_SUMMARIZATION_PROMPT,
    IMAGE_PROMPT_TEMPLATE,
    BUILD_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)

# Type constants to avoid magic strings
COMPOSITE_ELEMENT_TYPE = "CompositeElement"
TABLE_TYPE = "Table"
IMAGE_TYPE = "Image"

VECTORSTORE_PATH = Path(__file__).parent.parent / "vectorstore"
IMAGE_STORE_PATH = VECTORSTORE_PATH / "image_store"

class PDFProcessor:
    """Process and index PDFs from Google Classroom materials using advanced multi-model RAG"""

    def __init__(self, classroom_tool, retriever_k: int = 5, llm_temperature: float = 0.3, image_concurrency: int = 2):
        self.classroom_tool = classroom_tool
        self.retriever_k = retriever_k
        self.llm_temperature = llm_temperature
        self.image_concurrency = image_concurrency
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key= os.getenv("OPENAI_API_KEY")
        )
        self.vectorstore = Chroma(
            persist_directory= str(VECTORSTORE_PATH),
            embedding_function=self.embeddings, 
            collection_name= "classroom_multimodel_rag"
        )

        IMAGE_STORE_PATH.mkdir(parents= True, exist_ok=True)

        self.llm=ChatOpenAI(
            model="gpt-4o-mini",
            temperature=self.llm_temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        prompt_text=TEXT_TABLE_SUMMARIZATION_PROMPT

        prompt = ChatPromptTemplate.from_template(prompt_text)
        self.summarize_chain = {"element":lambda x:x} | prompt | self.llm | StrOutputParser()

        prompt_template = IMAGE_PROMPT_TEMPLATE

        messages = [
            (
                "user",
                [
                    {
                        "type":"text", "text":prompt_template
                    },
                    {
                        "type":"image_url",
                        "image_url":{"url":"data:image/jpeg;base64, {image}"}, # to embed an img in a str
                    },
                ]
            )
        ]

        image_prompt = ChatPromptTemplate.from_messages(messages)
        self.image_summarization_chain = image_prompt | ChatOpenAI(model= "gpt-4o-mini") | StrOutputParser()

    def _has_html_representation(self, chunk) -> bool:
        """Check if chunk has HTML table representation."""
        return (hasattr(chunk, "metadata") and 
                hasattr(chunk.metadata, "text_as_html") and
                getattr(chunk.metadata, "text_as_html", None) is not None)
    
    def _get_chunk_text(self, chunk) -> str:
        """Safely extract text from chunk."""
        return chunk.text if hasattr(chunk, "text") else str(chunk)
    
    def _is_type(self, obj, type_name: str) -> bool:
        """Check if object's type contains the given type name."""
        return type_name in str(type(obj))

    def _save_image_base64(self, image_b64: str) -> str:
        """Persist base64 image payload and return a stable unique key.
        """
        # Hash the image for deterministic retrieval
        digest = hashlib.sha256(image_b64.encode("utf-8")).hexdigest()[:16]
        # Add UUID to avoid collision
        image_key = f"img_{digest}_{uuid.uuid4().hex[:8]}"
        # Save to disk
        (IMAGE_STORE_PATH / f"{image_key}.b64").write_text(image_b64, encoding="utf-8")
        return image_key
        
    def _load_image_base64(self, image_key: str) -> Optional[str]:
        """Load a base64 image from disk by key.
        """
        path = IMAGE_STORE_PATH / f"{image_key}.b64"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
        
    def extract_multimodal_content(self, pdf_bytes: bytes, temp_filename: str) -> Dict:
        """Extract text, tables, and images from PDF using unstructured library.
        Args:
            pdf_bytes: Raw PDF file bytes
            temp_filename: Name for temporary PDF file during processing
        Returns:
            Dictionary with 'texts', 'tables', and 'images' keys containing extracted content
        """
        temp_path = VECTORSTORE_PATH / "temp" / temp_filename
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            temp_path.write_bytes(pdf_bytes)
            chunks = partition_pdf(
                filename=str(temp_path),
                strategy="hi_res",
                infer_table_structure=True,
                extract_image_block_types=["Image"],
                chunking_strategy="by_title",
                max_character=10000,
                combine_text_under_n_chars=20000,
                new_after_n_chars=6000,
            )
            
            # Extract images from composite elements
            images_b64 = []
            for chunk in chunks:
                if self._is_type(chunk, COMPOSITE_ELEMENT_TYPE):
                    if hasattr(chunk.metadata, "orig_elements"):
                        for el in chunk.metadata.orig_elements:
                            if self._is_type(el, IMAGE_TYPE):
                                if hasattr(el.metadata, "image_base64") and el.metadata.image_base64:
                                    images_b64.append(el.metadata.image_base64)
            
            tables: List[Dict[str, str]] = []
            texts = []
            
            for chunk in chunks:
                # Extract top-level tables with HTML or Table type
                if self._has_html_representation(chunk):
                    html = chunk.metadata.text_as_html
                    chunk_text = self._get_chunk_text(chunk)
                    tables.append({"html": str(html), "text": str(chunk_text)})
                elif self._is_type(chunk, TABLE_TYPE):
                    chunk_text = self._get_chunk_text(chunk)
                    tables.append({"html": "", "text": str(chunk_text)})
                
                # Extract nested tables from composite elements
                if self._is_type(chunk, COMPOSITE_ELEMENT_TYPE) and hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
                    for el in chunk.metadata.orig_elements or []:
                        if not self._is_type(el, TABLE_TYPE):
                            continue
                        el_html = getattr(el.metadata, "text_as_html", None) if hasattr(el, "metadata") and hasattr(el.metadata, "text_as_html") else None
                        el_text = self._get_chunk_text(el)
                        tables.append({"html": str(el_html or ""), "text": str(el_text)})
                    
                    # Add composite text elements
                    texts.append(chunk)
            
            return {"texts": texts, "tables": tables, "images": images_b64}
        
        except Exception as e:
            logger.error(f"Unstructured extraction failed: {e}")
            return {"texts": [], "tables": [], "images": []}
            
    def _add_to_vectorstore(self, items: List[str], base_metadata: Dict) -> int:
        """Add items to vectorstore with metadata.
        """
        docs: List[Document] = []
        for i, item in enumerate(items):
            if item and str(item).strip():
                docs.append(
                    Document(
                        page_content=str(item),
                        metadata={**base_metadata, "chunk_index": i},
                    )
                )
        if not docs:
            return 0
        self.vectorstore.add_documents(docs)
        return len(docs)

    def process_and_index_material(self, course_id: str, material: Dict) -> int:
        """Process and index PDFs with multi-modal content (text, tables, images).
        """
        material_id = material["id"]
        
        # Skip if material already indexed
        if self.vectorstore._collection.get(where={"material_id": material_id}, limit=1).get("ids"):
            return 0
        
        indexed = 0
        for attachment in material.get("material", []):
            if "driveFile" not in attachment:
                continue
            
            file = attachment["driveFile"]["driveFile"]
            if not file["title"].lower().endswith(".pdf"):
                continue
            
            logger.info(f"Processing PDF: {file['title']}")
            
            # download PDF from Google Drive
            pdf_bytes = self.classroom_tool.download_drive_pdf(file["id"])
            if not pdf_bytes:
                logger.warning(f"Failed to download PDF: {file['title']}")
                continue
            
            # extract multimodal content
            content = self.extract_multimodal_content(pdf_bytes, file["title"])
            
            if not any([content["texts"], content["tables"], content["images"]]):
                logger.warning(f"No content extracted from {file['title']}")
                continue
            
            logger.info(
                f"Extracted {len(content['texts'])} texts, "
                f"{len(content['tables'])} tables, "
                f"{len(content['images'])} images"
            )
            
            # process text chunks
            text_chunks = [t.text if hasattr(t, "text") else str(t) for t in content["texts"]]
            
            # process table chunks
            table_chunks = []
            for tbl in content["tables"]:
                if isinstance(tbl, dict):
                    table_chunks.append(str(tbl.get("html") or tbl.get("text") or ""))
                else:
                    table_text = (
                        tbl.metadata.text_as_html
                        if hasattr(tbl, "metadata")
                        and hasattr(tbl.metadata, "text_as_html")
                        and tbl.metadata.text_as_html
                        else (tbl.text if hasattr(tbl, "text") else str(tbl))
                    )
                    table_chunks.append(table_text)
            
            # summarize images 
            image_summaries = []
            if content["images"]:
                try:
                    logger.info(f"Summarizing {len(content['images'])} images")
                    image_summaries = self.image_summarization_chain.batch(
                        [{"image": img} for img in content["images"]],
                        {"max_concurrency": self.image_concurrency},
                    )
                except Exception as e:
                    logger.error(f"Error summarizing images: {e}")
                    image_summaries = []
            
            base_metadata = {
                "course_id": course_id,
                "material_id": material_id,
                "material_title": material.get("title", ""),
                "file_id": file["id"],
                "filename": file["title"],
                "source": "google_classroom",
            }
            
            # add text and table chunks
            indexed += self._add_to_vectorstore(text_chunks, {**base_metadata, "type": "text"})
            indexed += self._add_to_vectorstore(table_chunks, {**base_metadata, "type": "table"})
            
            # add image summaries with base64 references
            if content["images"] and image_summaries and len(image_summaries) == len(content["images"]):
                image_docs = []
                for i, (img_b64, img_summary) in enumerate(zip(content["images"], image_summaries)):
                    image_key = self._save_image_base64(img_b64)
                    image_docs.append(
                        Document(
                            page_content=img_summary,
                            metadata={
                                **base_metadata,
                                "type": "image",
                                "chunk_index": i,
                                "image_key": image_key,
                            },
                        )
                    )
                self.vectorstore.add_documents(image_docs)
                indexed += len(image_docs)
            
            logger.info(f"Indexed {indexed} items from {file['title']}")
        
        return indexed
    

    def process_course_materials(self, course_id: str) -> Dict[str, int]:
        """Process all materials (PDFs) for a given course.
        """
        materials = self.classroom_tool.list_coursework_materials(course_id)
        logger.info(f"Found {len(materials)} materials for course {course_id}")
        
        stats = {
            "materials_processed": len(materials),
            "pdfs_found": 0,
            "chunks_indexed": 0,
        }
        
        for material in materials:
            pdf_count = sum(
                1
                for m in material.get("material", [])
                if "driveFile" in m and m["driveFile"]["driveFile"]["title"].lower().endswith(".pdf")
            )
            stats["pdfs_found"] += pdf_count
            stats["chunks_indexed"] += self.process_and_index_material(course_id, material)
        
        return stats
    
    def get_retriever(self, k: Optional[int] = None, filter_dict: Optional[Dict] = None, use_mmr: bool = True):
        """Get a retriever from the vectorstore with optional filtering.
        
        Args:
            k: Number of results (uses self.retriever_k if not provided)
            filter_dict: Optional metadata filter
            use_mmr: Use MMR search for diversity
        """
        if k is None:
            k = self.retriever_k
            
        search_kwargs = {"k": k}
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        
        # For MMR, fetch more candidates to ensure diversity
        if use_mmr:
            search_kwargs["fetch_k"] = k * 3
        
        search_type = "mmr" if use_mmr else "similarity"
        return self.vectorstore.as_retriever(search_type=search_type, search_kwargs=search_kwargs)
    
    def _parse_retrieved_docs(self, docs: List[Document]) -> Dict:
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
            text_docs.append(Document(
                page_content=f"Image description: {summary}", 
                metadata={"type":"image_summary"}
            ))
        return {"images":b64_images, "texts":text_docs}
    
    def _build_multimodal_prompt(self, context: Dict, question: str):
        """Build multimodal prompt combining text context and images."""
        docs_by_type = context
        
        context_text = ""
        if docs_by_type["texts"]:
            for text_element in docs_by_type["texts"]:
                content = text_element.page_content if isinstance(text_element, Document) else str(text_element)
                context_text += content + "\n\n"
        
        prompt_template = BUILD_PROMPT_TEMPLATE
        prompt_content = [{"type": "text", "text": prompt_template}]
        
        if docs_by_type["images"]:
            for image in docs_by_type["images"]:
                prompt_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                })
        
        return ChatPromptTemplate.from_messages([HumanMessage(content=prompt_content)])
    
    def create_multi_modal_chain(self):
        """Create a RAG chain that handles text, tables, and images.
        """
        retriever = self.get_retriever()

        # build the RAG chain: retrieve -> parse -> build prompt -> LLM -> parse output
        chain = (
            {
                "context": retriever | RunnableLambda(self._parse_retrieved_docs),
                "question": RunnablePassthrough(),
            }
            | RunnableLambda(lambda x: self._build_multimodal_prompt(x["context"], x["question"]))
            | ChatOpenAI(model="gpt-4o-mini", temperature=self.llm_temperature)
            | StrOutputParser()
        )
        
        return chain


     

            


                    

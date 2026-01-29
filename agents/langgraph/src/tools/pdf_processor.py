import hashlib
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from unstructured.partition.pdf import partition_pdf

from agents.model import Model
from prompts.classroom import (
    BUILD_PROMPT_TEMPLATE,
    IMAGE_PROMPT_TEMPLATE,
    TEXT_TABLE_SUMMARIZATION_PROMPT,
)

VECTORSTORE_PATH = Path(__file__).parent.parent / "vectorstore"
IMAGE_STORE_PATH = VECTORSTORE_PATH / "image_store"
EMBEDDING_MODEL = "text-embedding-3-small"
IMAGE_MODEL = "gpt-4o-mini"
COLLECTION_NAME = "classroom_multimodal_rag"

PDF_EXTRACTION_CONFIG = {
    "strategy": "hi_res",
    "infer_table_structure": True,
    "extract_image_block_types": ["Image"],
    "extract_image_block_to_payload": True,
    "chunking_strategy": "by_title",
    "max_characters": 10000,
    "combine_text_under_n_chars": 2000,
    "new_after_n_chars": 6000,
}

TYPE_TEXT = "text"
TYPE_TABLE = "table"
TYPE_IMAGE = "image"
TYPE_IMAGE_SUMMARY = "image_summary"

model = Model()
class ImageStore:
    """Manages image storage and retrieval."""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.store_path.mkdir(parents=True, exist_ok=True)

    def save(self, image_b64: str) -> str:
        """Persist base64 image and return a stable key."""
        digest = hashlib.sha256(image_b64.encode("utf-8")).hexdigest()[:16]
        image_key = f"img_{digest}_{uuid.uuid4().hex[:8]}"
        (self.store_path / f"{image_key}.b64").write_text(image_b64, encoding="utf-8")
        return image_key

    def load(self, image_key: str) -> Optional[str]:
        """Retrieve base64 image by key."""
        path = self.store_path / f"{image_key}.b64"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")


class ContentExtractor:
    """Extracts multimodal content from PDFs."""

    @staticmethod
    def extract(pdf_bytes: bytes, temp_filename: str, temp_dir: Path) -> Dict:
        """Extract text, tables, and images from PDF."""
        temp_path = temp_dir / temp_filename
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            temp_path.write_bytes(pdf_bytes)
            chunks = partition_pdf(filename=str(temp_path), **PDF_EXTRACTION_CONFIG)
            return ContentExtractor._process_chunks(chunks)
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return {"texts": [], "tables": [], "images": []}
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @staticmethod
    def _process_chunks(chunks: List) -> Dict:
        """Process extracted chunks into texts, tables, and images."""
        images_b64 = ContentExtractor._extract_images(chunks)
        tables = ContentExtractor._extract_tables(chunks)
        texts = ContentExtractor._extract_texts(chunks)
        return {"texts": texts, "tables": tables, "images": images_b64}

    @staticmethod
    def _extract_images(chunks: List) -> List[str]:
        """Extract base64 images from chunks."""
        images_b64 = []
        for chunk in chunks:
            if "CompositeElement" not in str(type(chunk)):
                continue
            if not hasattr(chunk.metadata, "orig_elements"):
                continue
            for el in chunk.metadata.orig_elements:
                if "Image" in str(type(el)):
                    if hasattr(el.metadata, "image_base64") and el.metadata.image_base64:
                        images_b64.append(el.metadata.image_base64)
        return images_b64

    @staticmethod
    def _extract_tables(chunks: List) -> List[Dict[str, str]]:
        """Extract tables from chunks."""
        tables = []
        for chunk in chunks:
            if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "text_as_html"):
                html = getattr(chunk.metadata, "text_as_html", None)
                if html:
                    chunk_text = chunk.text if hasattr(chunk, "text") else str(chunk)
                    tables.append({"html": str(html), "text": str(chunk_text)})
                    continue

            if "Table" in str(type(chunk)):
                chunk_text = chunk.text if hasattr(chunk, "text") else str(chunk)
                tables.append({"html": "", "text": str(chunk_text)})
                continue

            if "CompositeElement" in str(type(chunk)):
                if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
                    for el in chunk.metadata.orig_elements or []:
                        if "Table" not in str(type(el)):
                            continue
                        el_html = None
                        if hasattr(el, "metadata") and hasattr(el.metadata, "text_as_html"):
                            el_html = getattr(el.metadata, "text_as_html", None)
                        el_text = el.text if hasattr(el, "text") else str(el)
                        tables.append({"html": str(el_html or ""), "text": str(el_text)})

        return tables

    @staticmethod
    def _extract_texts(chunks: List) -> List:
        """Extract text chunks."""
        text_types = {"CompositeElement", "Text", "NarrativeText", "Title", "ListItem", "Header", "Footer"}
        return [chunk for chunk in chunks if any(t in str(type(chunk)) for t in text_types)]


class ChainBuilder:
    """Builds LangChain chains for different tasks."""

    def __init__(self, llm, image_llm):
        self.llm = llm
        self.image_llm = image_llm

    def build_summarization_chain(self) -> object:
        """Build chain for summarizing tables and text."""
        prompt = ChatPromptTemplate.from_template(TEXT_TABLE_SUMMARIZATION_PROMPT)
        return {"element": lambda x: x} | prompt | self.llm | StrOutputParser()

    def build_image_summarization_chain(self) -> object:
        """Build chain for summarizing images."""
        messages = [
            (
                "user",
                [
                    {"type": "text", "text": IMAGE_PROMPT_TEMPLATE},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64,{image}"},
                    },
                ],
            )
        ]
        image_prompt = ChatPromptTemplate.from_messages(messages)
        return image_prompt | ChatOpenAI(model=IMAGE_MODEL) | StrOutputParser()


class PDFProcessor:
    """Process and index PDFs from Google Classroom with multimodal RAG."""

    def __init__(self, classroom_tool):
        self.classroom_tool = classroom_tool

        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.vectorstore = Chroma(
            persist_directory=str(VECTORSTORE_PATH),
            embedding_function=self.embeddings,
            collection_name=COLLECTION_NAME,
        )

        self.image_store = ImageStore(IMAGE_STORE_PATH)
        self.content_extractor = ContentExtractor()

        llm = model.openai_model
        self.summarize_chain = ChainBuilder(llm, ChatOpenAI(model=IMAGE_MODEL)).build_summarization_chain()
        self.image_summarization_chain = ChainBuilder(llm, ChatOpenAI(model=IMAGE_MODEL)).build_image_summarization_chain()

    def process_course_materials(self, course_id: str) -> Dict[str, int]:
        """Process all materials for a course."""
        materials = self.classroom_tool.list_coursework_materials(course_id)

        stats = {
            "materials_processed": len(materials),
            "pdfs_found": 0,
            "chunks_indexed": 0,
        }

        for material in materials:
            pdf_count = self._count_pdfs(material)
            stats["pdfs_found"] += pdf_count
            stats["chunks_indexed"] += self.process_and_index_material(course_id, material)

        return stats

    def process_and_index_material(self, course_id: str, material: Dict) -> int:
        """Process and index a single material with PDFs."""
        material_id = material["id"]

        if self._is_already_indexed(material_id):
            return 0

        indexed = 0
        for attachment in material.get("materials", []):
            indexed += self._process_pdf_attachment(course_id, material, attachment)

        return indexed

    def _process_pdf_attachment(self, course_id: str, material: Dict, attachment: Dict) -> int:
        """Process a single PDF attachment."""
        if "driveFile" not in attachment:
            return 0

        file = attachment["driveFile"]["driveFile"]
        if not file["title"].lower().endswith(".pdf"):
            return 0

        pdf_bytes = self.classroom_tool.download_drive_pdf(file["id"])
        if not pdf_bytes:
            return 0

        content = self.content_extractor.extract(pdf_bytes, file["title"], VECTORSTORE_PATH / "temp")

        if not any([content["texts"], content["tables"], content["images"]]):
            return 0

        base_metadata = self._build_metadata(course_id, material, file)
        indexed = 0

        text_chunks = self._extract_chunk_texts(content["texts"])
        indexed += self._add_to_vectorstore(text_chunks, {**base_metadata, "type": TYPE_TEXT})

        table_chunks = self._extract_table_texts(content["tables"])
        indexed += self._add_to_vectorstore(table_chunks, {**base_metadata, "type": TYPE_TABLE})

        indexed += self._process_images(content["images"], base_metadata)

        return indexed

    def _process_images(self, images: List[str], base_metadata: Dict) -> int:
        """Process and index image summaries."""
        if not images:
            return 0

        try:
            summaries = self.image_summarization_chain.batch(
                [{"image": img} for img in images],
                {"max_concurrency": 2},
            )
        except Exception as e:
            print(f"Error summarizing images: {e}")
            return 0

        if len(summaries) != len(images):
            return 0

        image_docs = []
        for i, (img_b64, summary) in enumerate(zip(images, summaries)):
            image_key = self.image_store.save(img_b64)
            image_docs.append(
                Document(
                    page_content=summary,
                    metadata={
                        **base_metadata,
                        "type": TYPE_IMAGE,
                        "chunk_index": i,
                        "image_key": image_key,
                    },
                )
            )

        self.vectorstore.add_documents(image_docs)
        return len(image_docs)

    def _add_to_vectorstore(self, items: List[str], metadata: Dict) -> int:
        """Add items to vectorstore."""
        docs = [
            Document(page_content=str(item), metadata={**metadata, "chunk_index": i})
            for i, item in enumerate(items)
            if item and str(item).strip()
        ]

        if not docs:
            return 0

        try:
            self.vectorstore.add_documents(docs)
            return len(docs)
        except Exception as e:
            print(f"Error adding documents to vectorstore: {e}")
            return 0

    def get_retriever(self, k: int = 5, filter_dict: Optional[Dict] = None, use_mmr: bool = True):
        """Get a retriever from the vector store."""
        search_kwargs = {"k": k}
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        if use_mmr:
            search_kwargs["fetch_k"] = k * 3

        search_type = "mmr" if use_mmr else "similarity"
        return self.vectorstore.as_retriever(search_type=search_type, search_kwargs=search_kwargs)

    def create_rag_chain(self):
        """Create a multimodal RAG chain."""
        retriever = self.get_retriever(k=5)
        return (
            {
                "context": retriever | RunnableLambda(self._parse_retrieved_docs),
                "question": RunnablePassthrough(),
            }
            | RunnableLambda(self._build_multimodal_prompt)
            | ChatOpenAI(model=IMAGE_MODEL)
            | StrOutputParser()
        )

    def _parse_retrieved_docs(self, docs: List[Document]) -> Dict:
        """Parse retrieved documents into images and text."""
        b64_images = []
        text_docs = []
        image_summaries = []

        for doc in docs:
            if not isinstance(doc, Document):
                continue

            doc_type = doc.metadata.get("type")
            if doc_type == TYPE_IMAGE:
                image_summaries.append(doc.page_content)
                image_key = doc.metadata.get("image_key")
                if image_key:
                    img_b64 = self.image_store.load(str(image_key))
                    if img_b64:
                        b64_images.append(img_b64)
            else:
                text_docs.append(doc)

        for summary in image_summaries:
            text_docs.append(
                Document(page_content=f"Image description: {summary}", metadata={"type": TYPE_IMAGE_SUMMARY})
            )

        return {"images": b64_images, "texts": text_docs}

    def _build_multimodal_prompt(self, kwargs: Dict) -> ChatPromptTemplate:
        """Build a multimodal prompt with text and images."""
        docs_by_type = kwargs["context"]
        user_question = kwargs["question"]

        context_text = self._format_context_text(docs_by_type["texts"])
        prompt_content = [{"type": "text", "text": BUILD_PROMPT_TEMPLATE.format(context=context_text, question=user_question)}]

        for image in docs_by_type["images"]:
            prompt_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"},
            })

        return ChatPromptTemplate.from_messages([HumanMessage(content=prompt_content)])


    @staticmethod
    def _count_pdfs(material: Dict) -> int:
        """Count PDF files in a material."""
        return sum(
            1
            for m in material.get("materials", [])
            if "driveFile" in m and m["driveFile"]["driveFile"]["title"].lower().endswith(".pdf")
        )

    @staticmethod
    def _build_metadata(course_id: str, material: Dict, file: Dict) -> Dict:
        """Build metadata for indexed documents."""
        return {
            "course_id": course_id,
            "material_id": material["id"],
            "material_title": material.get("title", ""),
            "file_id": file["id"],
            "filename": file["title"],
            "source": "google_classroom",
        }

    @staticmethod
    def _extract_chunk_texts(chunks: List) -> List[str]:
        """Extract text from chunk objects."""
        return [c.text if hasattr(c, "text") else str(c) for c in chunks]

    @staticmethod
    def _extract_table_texts(tables: List[Dict]) -> List[str]:
        """Extract text from table objects."""
        texts = []
        for tbl in tables:
            if isinstance(tbl, dict):
                texts.append(str(tbl.get("html") or tbl.get("text") or ""))
            else:
                text = (
                    tbl.metadata.text_as_html
                    if hasattr(tbl, "metadata")
                    and hasattr(tbl.metadata, "text_as_html")
                    and tbl.metadata.text_as_html
                    else (tbl.text if hasattr(tbl, "text") else str(tbl))
                )
                texts.append(text)
        return texts

    @staticmethod
    def _format_context_text(text_docs: List[Document]) -> str:
        """Format text documents into a single context string."""
        context_parts = []
        for doc in text_docs:
            content = doc.page_content if isinstance(doc, Document) else str(doc)
            context_parts.append(content)
        return "\n\n".join(context_parts)

    def _is_already_indexed(self, material_id: str) -> bool:
        """Check if material is already in vectorstore."""
        try:
            result = self.vectorstore._collection.get(where={"material_id": material_id}, limit=1)
            return bool(result.get("ids"))
        except Exception:
            return False
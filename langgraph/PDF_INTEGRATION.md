# PDF Integration with Google Classroom

## Overview

Your Voicera system can now automatically fetch, process, and answer questions about PDFs uploaded to Google Classroom. The system:

1. **Fetches course materials** from Google Classroom using the courseWorkMaterials API
2. **Downloads PDFs** from Google Drive attachments
3. **Extracts and chunks text** from PDFs using pypdf
4. **Indexes content** into ChromaDB vector store
5. **Retrieves relevant context** when students ask questions

## What Changed

### New Files Created

- **`src/tools/pdf_processor.py`** - Handles PDF downloading, text extraction, chunking, and indexing
- **`test_pdf_integration.py`** - Test script to verify the integration

### Modified Files

- **`src/tools/classroomTools.py`**

  - Added Google Drive API scope (`drive.readonly`)
  - Added `list_coursework_materials()` method to fetch materials
  - Added `download_drive_pdf()` method to download PDFs from Drive
  - Fixed missing comma in SCOPES array

- **`src/agents/eureka/state.py`**

  - Added `CourseWorkMaterial` model to represent materials
  - Added `materials` field to `GraphState`

- **`src/agents/eureka/nodes.py`**

  - Added `load_and_index_materials()` node to process PDFs
  - Enhanced `generate_ai_response()` to retrieve PDF context from vector store

- **`src/agents/eureka/graph.py`**

  - Added `load_and_index_materials` node to workflow
  - Updated workflow edges to include materials processing

- **`pyproject.toml`**
  - Added `pypdf>=4.0.0` for PDF text extraction
  - Added `langchain-text-splitters>=0.3.0` for text chunking

## How It Works

### Workflow

```
1. load_courses → Fetch Google Classroom courses
2. load_coursework → Fetch assignments
3. load_and_index_materials → NEW! Fetch materials with PDFs
   ├─ Download PDFs from Google Drive
   ├─ Extract text using pypdf
   ├─ Chunk text (1000 chars, 200 overlap)
   └─ Index into ChromaDB with metadata
4. receive_student_query → Process student question
5. categorize_query → Classify question type
6. construct_rag_queries → Generate guidance
7. generate_ai_response → NEW! Retrieve PDF context + Generate answer
8. verify_ai_response → Quality check
```

### PDF Metadata Stored

Each PDF chunk is indexed with:

- `course_id` - Course identifier
- `material_id` - Material identifier
- `material_title` - Title of the material
- `file_id` - Google Drive file ID
- `filename` - PDF filename
- `chunk_index` - Chunk position
- `source` - "google_classroom"
- `type` - "pdf_material"

### Smart Caching

The system checks if materials are already indexed before re-processing, avoiding redundant downloads and processing.

## Setup Instructions

### 1. Re-authenticate with Google (REQUIRED)

Since we added the Drive API scope, you need to re-authenticate:

```bash
cd C:\Users\user\Desktop\Voicera\langgraph
# Delete existing token to force re-authentication
rm token.json
```

Next time you run the agent, it will open a browser for you to grant Drive permissions.

### 2. Install Dependencies

Dependencies should already be installed, but if needed:

```bash
C:/Users/user/Desktop/Voicera/.venv/Scripts/python.exe -m pip install pypdf langchain-text-splitters
```

### 3. Test the Integration

Run the test script to verify everything works:

```bash
cd C:\Users\user\Desktop\Voicera\langgraph
C:/Users/user/Desktop/Voicera/.venv/Scripts/python.exe test_pdf_integration.py
```

This will:

- Authenticate with Google Classroom and Drive
- List your courses
- Fetch materials from the first course
- Identify PDFs
- Test downloading a PDF
- Initialize the PDF processor

### 4. Run the Agent

The PDF processing is now automatic. When a student asks a question:

```python
# Via API (existing endpoint)
POST http://localhost:8000/ask
{
    "student_question": "What topics are covered in the lecture notes?",
    "course_id": "optional_course_id"
}
```

The agent will:

1. Process all course materials (PDFs) on first run
2. Retrieve relevant PDF chunks based on the question
3. Include PDF content in the AI response generation
4. Provide answers grounded in the PDF materials

## Configuration Options

### Chunk Size and Overlap

Edit `src/tools/pdf_processor.py`:

```python
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,     # Characters per chunk (adjust for longer docs)
    chunk_overlap=200,   # Overlap between chunks
)
```

### Retrieval Count

Edit `src/agents/eureka/nodes.py` in `generate_ai_response()`:

```python
retriever = self.pdf_processor.get_retriever(
    k=3,  # Number of PDF chunks to retrieve (increase for more context)
    filter_dict={"course_id": course_id}
)
```

### Course Filtering

Currently, the system only retrieves PDFs from the student's current course. To search across all courses:

```python
# Remove the filter_dict parameter
retriever = self.pdf_processor.get_retriever(k=3)
```

## Troubleshooting

### "Permission denied" errors

- Ensure PDFs are shared with the service account
- Check that the Google Drive API scope is included
- Re-authenticate by deleting `token.json`

### No PDFs found

- Verify materials are uploaded to Google Classroom (not just coursework)
- Check they are in the "Materials" section, not "Assignments"
- Use `test_pdf_integration.py` to debug

### PDF text extraction fails

- Some PDFs are image-based (scanned documents)
- Consider adding OCR support with `pytesseract` if needed
- Check PDF is not password-protected

### Vector store errors

- Ensure `OPENAI_API_KEY` is set in `.env`
- Check ChromaDB directory exists: `src/vectorstore/`
- Verify disk space for large PDF collections

## API Changes

No breaking changes to existing API endpoints. The `/ask` endpoint now automatically:

- Processes PDFs on first run per course
- Includes PDF context in responses
- Caches processed materials

## Performance Considerations

### First Run per Course

- Downloads all PDFs (~10-30 seconds per course)
- Extracts and chunks text (~5-10 seconds per PDF)
- Indexes into vector store (~2-5 seconds)

### Subsequent Runs

- Checks if materials already indexed (instant)
- Only processes new/updated materials

### Large Courses

- For courses with 50+ PDFs, consider:
  - Pre-processing materials with a separate endpoint
  - Increasing chunk size to reduce index size
  - Implementing batch processing

## Next Steps

Consider these enhancements:

1. **Add a /index-materials endpoint** for manual pre-processing
2. **Support Google Docs/Slides** (export to PDF first)
3. **Add OCR for scanned PDFs** using pytesseract
4. **Implement incremental updates** (only re-index changed PDFs)
5. **Add material search endpoint** to query PDFs directly
6. **Track material usage** in responses for analytics

## Example Usage

```python
from tools.classroomTools import ClassroomTool
from tools.pdf_processor import PDFProcessor

# Initialize
tool = ClassroomTool()
processor = PDFProcessor(tool)

# Process a course
stats = processor.process_course_materials("course_id_123")
print(f"Indexed {stats['chunks_indexed']} chunks from {stats['pdfs_found']} PDFs")

# Query the vector store
retriever = processor.get_retriever(k=5, filter_dict={"course_id": "course_id_123"})
docs = retriever.get_relevant_documents("What is photosynthesis?")

for doc in docs:
    print(f"From {doc.metadata['filename']}:")
    print(doc.page_content[:200])
```

## Questions?

If you encounter issues:

1. Run `test_pdf_integration.py` for diagnostics
2. Check the logs for error messages
3. Verify Google Drive permissions
4. Ensure PDFs are accessible (not private)

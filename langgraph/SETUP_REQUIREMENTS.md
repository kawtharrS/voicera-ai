# Additional Setup Requirements for Advanced PDF Processing

## System Dependencies

The new multi-modal PDF processing system requires two external tools:

### 1. Tesseract OCR (for image text extraction)

- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Install to default location: `C:\Program Files\Tesseract-OCR`
- Add to PATH: `C:\Program Files\Tesseract-OCR`

### 2. Poppler (for PDF to image conversion)

- **Windows**: Download from https://github.com/oschwartz10612/poppler-windows/releases
- Extract to: `C:\Program Files\poppler`
- Add to PATH: `C:\Program Files\poppler\Library\bin`

## Python Dependencies

Already installed via pip:

```bash
pip install unstructured[pdf] pdf2image pillow
```

## Verification

Test if everything is installed:

```python
import pytesseract
from pdf2image import convert_from_path
from unstructured.partition.pdf import partition_pdf

print("✓ All dependencies installed!")
```

## Features Enabled

With this setup, your system now:

- ✅ Extracts text from complex PDFs with tables
- ✅ Processes images embedded in PDFs
- ✅ Handles scanned documents (OCR)
- ✅ Summarizes content using GPT-4o-mini
- ✅ Uses MultiVectorRetriever (searches summaries, returns full content)
- ✅ Separates text, tables, and images for better retrieval

## Fallback

If external tools aren't installed, the system will log warnings but continue with basic PDF text extraction using pypdf.

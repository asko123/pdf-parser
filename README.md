# PDF Content Extractor

A Python application that processes PDF files and extracts structured content including text, tables (with complex structures like merged cells), and images (with optional OCR text extraction).

## Features

- **Text Extraction**: Extracts all text content from each PDF page
- **Table Extraction**: Extracts tables with support for complex structures including merged cells and nested tables
- **Image Extraction**: Extracts images with descriptive context and optional OCR text extraction
- **Multiple OCR Backends**: Supports different OCR options including pip-only solutions (no system dependencies required)

## Installation

### Prerequisites

- Python 3.10+

### Python Dependencies

```bash
pip install -r requirements.txt
```

### Optional: OCR Support

The extractor supports multiple OCR backends. Choose based on your environment:

**Option 1: No OCR (default)** - No additional dependencies needed. Images will have `ocr_text: null`.

**Option 2: EasyOCR (pip-only, no system dependencies)**
```bash
pip install easyocr
```
Note: EasyOCR pulls in PyTorch (~2GB). First run downloads OCR models.

**Option 3: Tesseract (requires system installation)**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# macOS
brew install tesseract

# Then install Python bindings
pip install pytesseract
```

## Usage

```bash
python pdf_extractor.py <pdf_file> [output_file] [--ocr-backend BACKEND]
```

Arguments:
- `pdf_file`: Path to the PDF file to process
- `output_file`: Optional path to save JSON output (default: stdout)
- `--ocr-backend`: OCR backend to use: `none` (default), `easyocr`, or `tesseract`
- `--list-backends`: List available OCR backends and exit

### Examples

```bash
# Basic extraction (no OCR)
python pdf_extractor.py document.pdf output.json

# With EasyOCR (pip-only, no system dependencies)
python pdf_extractor.py document.pdf output.json --ocr-backend easyocr

# With Tesseract (requires system installation)
python pdf_extractor.py document.pdf output.json --ocr-backend tesseract

# Using environment variable
PDF_EXTRACTOR_OCR_BACKEND=easyocr python pdf_extractor.py document.pdf

# Check available backends
python pdf_extractor.py --list-backends
```

## Output Schema

The extractor outputs a JSON array with one object per page:

```json
{
  "page_number": integer,
  "text": string or null,
  "tables": [
    {
      "table_id": string,
      "structure": {
        "rows": [["cell1", "cell2", ...], ...],
        "merged_cells": [
          {"row": int, "col": int, "rowspan": int, "colspan": int}
        ]
      }
    }
  ],
  "images": [
    {
      "image_id": string,
      "description": string,
      "ocr_text": string or null
    }
  ]
}
```

## Data Population Rules

- If a page lacks extractable content for any field, the value is set to `null` (for text/OCR text) or an empty array (for tables/images)
- Field order is strictly maintained: `page_number`, `text`, `tables`, `images`
- All values adhere to the specified data types
- Tables with complex structures include detailed cell arrangements under `merged_cells`

## Dependencies

### Core (required)
- PyMuPDF (fitz): PDF parsing and image extraction
- pdfplumber: Text and table extraction
- Pillow: Image processing

### Optional (for OCR)
- easyocr: Pure Python OCR (pip install easyocr)
- pytesseract: Tesseract Python bindings (requires system Tesseract)

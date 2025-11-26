# PDF Extractor - Complete Execution Guide

**Version:** 1.0  
**Last Updated:** November 26, 2025

A comprehensive step-by-step guide to installing, configuring, and using the PDF Content Extractor.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Verification](#3-verification)
4. [Basic Usage](#4-basic-usage)
5. [Advanced Usage](#5-advanced-usage)
6. [OCR Configuration](#6-ocr-configuration)
7. [Real-World Examples](#7-real-world-examples)
8. [Output Analysis](#8-output-analysis)
9. [Troubleshooting](#9-troubleshooting)
10. [Best Practices](#10-best-practices)

---

## 1. Prerequisites

### Step 1.1: Check Python Version

```bash
python --version
# or
python3 --version
```

**Required:** Python 3.10 or higher

**If Python is not installed:**
- **macOS:** `brew install python@3.11`
- **Ubuntu/Debian:** `sudo apt install python3.11`
- **Windows:** Download from [python.org](https://python.org)

### Step 1.2: Verify pip

```bash
pip --version
# or
pip3 --version
```

**If pip is not available:**
```bash
python -m ensurepip --upgrade
```

### Step 1.3: (Optional) Create Virtual Environment

**Recommended to avoid dependency conflicts:**

```bash
# Navigate to your project directory
cd /path/to/pdf-extractor

# Create virtual environment
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

**You should see `(venv)` in your terminal prompt.**

---

## 2. Installation

### Step 2.1: Install Core Dependencies

```bash
# Make sure you're in the pdf-extractor directory
cd /path/to/pdf-extractor

# Install required packages
pip install -r requirements.txt
```

**What gets installed:**
- `PyMuPDF` (fitz) - PDF parsing and image extraction
- `pdfplumber` - Text and table extraction
- `Pillow` - Image processing

**Expected output:**
```
Successfully installed PyMuPDF-1.23.x pdfplumber-0.10.x Pillow-10.x.x
```

### Step 2.2: Verify Core Installation

```bash
python -c "import fitz, pdfplumber; from PIL import Image; print('✅ Core dependencies installed successfully!')"
```

**If successful, you'll see:**
```
✅ Core dependencies installed successfully!
```

### Step 2.3: (Optional) Install OCR Support

**Choose ONE option based on your needs:**

#### Option A: No OCR (Default)
```bash
# No additional installation needed
# Images will have ocr_text: null
```

#### Option B: EasyOCR (Pure Python, No System Dependencies)
```bash
# Install with NumPy compatibility fix
pip install "numpy<2" easyocr

# This installs ~2GB of dependencies (PyTorch)
# First run will download OCR models (~100MB)
```

#### Option C: Tesseract (Requires System Installation)
```bash
# First install Tesseract system-wide:

# macOS:
brew install tesseract

# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Windows:
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

# Then install Python wrapper:
pip install pytesseract
```

---

## 3. Verification

### Step 3.1: Check Available Backends

```bash
python pdf_extractor.py --list-backends
```

**Expected output:**
```
Available OCR backends:
  none: available
  easyocr: available     # (if installed)
  tesseract: available   # (if installed)
```

### Step 3.2: Verify with Help Command

```bash
python pdf_extractor.py --help
```

**You should see:**
```
usage: pdf_extractor.py [-h] [--ocr-backend {none,easyocr,tesseract}] 
                        [--list-backends] [pdf_file] [output_file]

Extract structured content from PDF files.
...
```

### Step 3.3: Run Quick Test

```bash
# Test with the included test document
python pdf_extractor.py test_document.pdf test_output.json
```

**Expected output:**
```
Extracting content from: test_document.pdf
OCR backend: none
Processing page 1/2...
Processing page 2/2...
Validating output schema...
Validation passed.
Output saved to: test_output.json
Successfully processed 2 page(s).
```

✅ **If you see this, installation is complete!**

---

## 4. Basic Usage

### Step 4.1: Extract PDF to JSON (Output to File)

```bash
python pdf_extractor.py input.pdf output.json
```

**What happens:**
1. Reads `input.pdf`
2. Extracts text, tables, and images from each page
3. Validates the output schema
4. Saves JSON to `output.json`

### Step 4.2: Extract PDF to stdout (Print to Terminal)

```bash
python pdf_extractor.py input.pdf
```

**Output goes to terminal** (useful for piping to other commands)

### Step 4.3: Extract with OCR

```bash
python pdf_extractor.py input.pdf output.json --ocr-backend easyocr
```

**What changes:**
- Images are processed with OCR
- `ocr_text` field contains extracted text from images
- First run downloads models (1-2 minutes)

### Step 4.4: Basic Workflow

```
┌─────────────┐
│  input.pdf  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ pdf_extractor.py│
│  (processes)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  output.json    │
│  (structured)   │
└─────────────────┘
```

---

## 5. Advanced Usage

### Step 5.1: Set Default OCR Backend via Environment Variable

```bash
# Set for current session
export PDF_EXTRACTOR_OCR_BACKEND=easyocr

# Now run without --ocr-backend flag
python pdf_extractor.py document.pdf output.json
```

**Add to shell profile for permanent setting:**
```bash
# For bash: ~/.bashrc or ~/.bash_profile
# For zsh: ~/.zshrc
echo 'export PDF_EXTRACTOR_OCR_BACKEND=easyocr' >> ~/.zshrc
source ~/.zshrc
```

### Step 5.2: Process Multiple PDFs

```bash
# Using a loop (bash)
for pdf in *.pdf; do
    echo "Processing $pdf..."
    python pdf_extractor.py "$pdf" "${pdf%.pdf}.json"
done
```

### Step 5.3: Process with Progress Tracking

```bash
# Create a processing script
cat > process_batch.sh << 'EOF'
#!/bin/bash
for pdf in *.pdf; do
    echo "================================"
    echo "Processing: $pdf"
    echo "================================"
    python pdf_extractor.py "$pdf" "${pdf%.pdf}.json"
    if [ $? -eq 0 ]; then
        echo "✅ Success: $pdf"
    else
        echo "❌ Failed: $pdf"
    fi
    echo ""
done
EOF

chmod +x process_batch.sh
./process_batch.sh
```

### Step 5.4: Extract and Analyze

```bash
# Extract
python pdf_extractor.py document.pdf output.json

# Analyze with Python
python << 'EOF'
import json

with open('output.json') as f:
    data = json.load(f)

print(f"Pages: {len(data)}")
print(f"Total images: {sum(len(p['images']) for p in data)}")
print(f"Total tables: {sum(len(p['tables']) for p in data)}")
EOF
```

---

## 6. OCR Configuration

### Step 6.1: First-Time OCR Setup

**Using EasyOCR:**

```bash
# Step 1: Install
pip install "numpy<2" easyocr

# Step 2: First run (downloads models)
python pdf_extractor.py test_document.pdf test_ocr.json --ocr-backend easyocr
```

**Expected first-run output:**
```
Extracting content from: test_document.pdf
OCR backend: easyocr
Initializing EasyOCR (first run may download models)...
Using CPU. Note: This module is much faster with a GPU.
Downloading detection model, please wait...
Progress: |████████████████████| 100.0% Complete
Downloading recognition model, please wait...
Progress: |████████████████████| 100.0% Complete
Processing page 1/2...
...
```

### Step 6.2: Compare OCR Backends

```bash
# Without OCR
python pdf_extractor.py document.pdf output_no_ocr.json

# With EasyOCR
python pdf_extractor.py document.pdf output_easyocr.json --ocr-backend easyocr

# With Tesseract (if installed)
python pdf_extractor.py document.pdf output_tesseract.json --ocr-backend tesseract

# Compare results
ls -lh output_*.json
```

### Step 6.3: OCR Performance Tips

**For faster processing:**
1. Use GPU if available (EasyOCR auto-detects)
2. Process smaller batches
3. Use Tesseract for simple text (faster than EasyOCR)

**For better accuracy:**
1. Use high-resolution PDFs
2. Use EasyOCR for complex fonts/languages
3. Ensure good image quality

---

## 7. Real-World Examples

### Example 7.1: Simple Document

**Scenario:** Extract text and tables from a business report

```bash
# Step 1: Extract
python pdf_extractor.py business_report.pdf report_data.json

# Step 2: View results
python -m json.tool report_data.json | less

# Step 3: Extract just table data
python << 'EOF'
import json

with open('report_data.json') as f:
    data = json.load(f)

for page in data:
    for table in page['tables']:
        print(f"\n{table['table_id']}:")
        for row in table['structure']['rows']:
            print(row)
EOF
```

### Example 7.2: AWS Architecture Diagram

**Scenario:** Extract diagrams and text from technical documentation

```bash
# Step 1: Extract images and text (without OCR)
python pdf_extractor.py aws_architecture_diagram.pdf aws_output.json

# Step 2: Extract with OCR to get labels from diagrams
python pdf_extractor.py aws_architecture_diagram.pdf aws_output_ocr.json --ocr-backend easyocr

# Step 3: Count extracted content
python << 'EOF'
import json

with open('aws_output_ocr.json') as f:
    data = json.load(f)

print(f"Pages: {len(data)}")
print(f"Images: {sum(len(p['images']) for p in data)}")
print(f"Images with OCR text: {sum(1 for p in data for img in p['images'] if img['ocr_text'])}")
EOF
```

### Example 7.3: Invoice Processing

**Scenario:** Extract invoice data including tables and images

```bash
# Process invoice with OCR
python pdf_extractor.py invoice_2025_001.pdf invoice_data.json --ocr-backend easyocr

# Extract invoice details
python << 'EOF'
import json

with open('invoice_data.json') as f:
    data = json.load(f)

# Extract text
for page in data:
    if page['text']:
        print("Invoice Text:")
        print(page['text'])
    
    # Extract tables
    for table in page['tables']:
        print(f"\nTable: {table['table_id']}")
        for row in table['structure']['rows']:
            print(" | ".join(row))
    
    # Check images for stamps/signatures
    for img in page['images']:
        if img['ocr_text']:
            print(f"\nImage OCR: {img['ocr_text']}")
EOF
```

### Example 7.4: Multi-Page Scientific Paper

**Scenario:** Extract content from research paper with equations and figures

```bash
# Step 1: Extract all content
python pdf_extractor.py research_paper.pdf paper_data.json --ocr-backend easyocr

# Step 2: Analyze structure
python << 'EOF'
import json

with open('paper_data.json') as f:
    data = json.load(f)

print("Paper Structure:")
for page in data:
    print(f"\nPage {page['page_number']}:")
    print(f"  Text: {len(page['text'])} characters" if page['text'] else "  Text: None")
    print(f"  Tables: {len(page['tables'])}")
    print(f"  Figures: {len(page['images'])}")
EOF
```

---

## 8. Output Analysis

### Step 8.1: Understanding the Output Schema

**JSON Structure:**
```json
[
  {
    "page_number": 1,
    "text": "string or null",
    "tables": [
      {
        "table_id": "table_p1_t1",
        "structure": {
          "rows": [["cell1", "cell2"], ["cell3", "cell4"]],
          "merged_cells": [
            {"row": 0, "col": 0, "rowspan": 1, "colspan": 2}
          ]
        }
      }
    ],
    "images": [
      {
        "image_id": "image_p1_i1",
        "description": "Image 1: A large color wide/landscape image (1920x1080 pixels, PNG format)",
        "ocr_text": "string or null"
      }
    ]
  }
]
```

### Step 8.2: Query Specific Data

**Extract all text:**
```bash
python << 'EOF'
import json

with open('output.json') as f:
    data = json.load(f)

all_text = []
for page in data:
    if page['text']:
        all_text.append(page['text'])

print("\n\n".join(all_text))
EOF
```

**Extract all table data:**
```bash
python << 'EOF'
import json

with open('output.json') as f:
    data = json.load(f)

for page in data:
    for table in page['tables']:
        print(f"\n{table['table_id']}:")
        for row in table['structure']['rows']:
            print("\t".join(row))
        print()
EOF
```

**List all images:**
```bash
python << 'EOF'
import json

with open('output.json') as f:
    data = json.load(f)

for page in data:
    for img in page['images']:
        print(f"{img['image_id']}: {img['description']}")
        if img['ocr_text']:
            print(f"  OCR: {img['ocr_text'][:50]}...")
EOF
```

### Step 8.3: Generate Summary Report

```bash
python << 'EOF'
import json

with open('output.json') as f:
    data = json.load(f)

print("=" * 60)
print("PDF EXTRACTION SUMMARY")
print("=" * 60)
print(f"Total Pages: {len(data)}")
print(f"Total Text Characters: {sum(len(p['text']) for p in data if p['text']):,}")
print(f"Total Tables: {sum(len(p['tables']) for p in data)}")
print(f"Total Images: {sum(len(p['images']) for p in data)}")
print()

for page in data:
    print(f"Page {page['page_number']}:")
    print(f"  Text: {len(page['text'])} chars" if page['text'] else "  Text: None")
    print(f"  Tables: {len(page['tables'])}")
    print(f"  Images: {len(page['images'])}")
EOF
```

---

## 9. Troubleshooting

### Issue 9.1: "ModuleNotFoundError: No module named 'fitz'"

**Problem:** PyMuPDF not installed

**Solution:**
```bash
pip install PyMuPDF>=1.23.0
```

### Issue 9.2: "NumPy 1.x cannot be run in NumPy 2.x"

**Problem:** NumPy version incompatibility with EasyOCR

**Solution:**
```bash
pip uninstall numpy
pip install "numpy<2"
```

### Issue 9.3: "FileNotFoundError: PDF file not found"

**Problem:** Incorrect file path

**Solution:**
```bash
# Check current directory
pwd
ls -la

# Use absolute path
python pdf_extractor.py /full/path/to/document.pdf output.json

# Or navigate to PDF directory first
cd /path/to/pdfs
python /path/to/pdf_extractor.py document.pdf output.json
```

### Issue 9.4: "TesseractNotFoundError"

**Problem:** Tesseract not installed system-wide

**Solution:**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Then verify
tesseract --version
```

### Issue 9.5: EasyOCR is Very Slow

**Problem:** Running on CPU instead of GPU

**Solutions:**
- Accept slower speed (CPU mode is normal)
- Use smaller PDFs
- Switch to Tesseract for simple text: `--ocr-backend tesseract`
- Use GPU-enabled machine

### Issue 9.6: "Validation Error: Field order mismatch"

**Problem:** Code modification broke schema

**Solution:**
```bash
# Re-download original pdf_extractor.py
# Or check that page dictionaries maintain order:
# page_number, text, tables, images
```

### Issue 9.7: Out of Memory Error

**Problem:** Processing very large PDF with many images

**Solution:**
```bash
# Process smaller batches
# Or increase system memory
# Or extract pages separately using PyMuPDF first
```

### Issue 9.8: Empty Output / No Content Extracted

**Problem:** PDF might be image-based or encrypted

**Diagnosis:**
```bash
# Check if PDF has selectable text
# Open in PDF viewer and try to select text
```

**Solution:**
```bash
# Use OCR for image-based PDFs
python pdf_extractor.py document.pdf output.json --ocr-backend easyocr

# For encrypted PDFs, decrypt first
```

---

## 10. Best Practices

### Practice 10.1: Workflow Organization

```
project/
├── input/           # Source PDFs
├── output/          # Generated JSON
├── scripts/         # Processing scripts
└── logs/           # Processing logs
```

**Processing script:**
```bash
#!/bin/bash
INPUT_DIR="input"
OUTPUT_DIR="output"
LOG_FILE="logs/processing_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$OUTPUT_DIR" "logs"

for pdf in "$INPUT_DIR"/*.pdf; do
    filename=$(basename "$pdf" .pdf)
    echo "Processing: $filename" | tee -a "$LOG_FILE"
    
    python pdf_extractor.py "$pdf" "$OUTPUT_DIR/${filename}.json" \
        --ocr-backend easyocr 2>&1 | tee -a "$LOG_FILE"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "✅ Success: $filename" | tee -a "$LOG_FILE"
    else
        echo "❌ Failed: $filename" | tee -a "$LOG_FILE"
    fi
    echo "" | tee -a "$LOG_FILE"
done
```

### Practice 10.2: Version Control

```bash
# Track your JSON outputs
git init
echo "*.pdf" >> .gitignore  # Don't commit large PDFs
echo "venv/" >> .gitignore
echo "__pycache__/" >> .gitignore

# Commit JSON outputs for tracking changes
git add output/*.json
git commit -m "Extracted content from batch 2025-11-26"
```

### Practice 10.3: Validation Workflow

```bash
# Always validate after extraction
python << 'EOF'
import json
import sys

try:
    with open('output.json') as f:
        data = json.load(f)
    
    # Validate schema
    for page in data:
        assert 'page_number' in page
        assert 'text' in page
        assert 'tables' in page
        assert 'images' in page
    
    print("✅ Validation passed")
    sys.exit(0)
except Exception as e:
    print(f"❌ Validation failed: {e}")
    sys.exit(1)
EOF
```

### Practice 10.4: Performance Optimization

**For large batches:**
```bash
# Process in parallel (requires GNU parallel)
ls input/*.pdf | parallel -j 4 \
    'python pdf_extractor.py {} output/{/.}.json'

# Or with xargs
find input -name "*.pdf" -print0 | \
    xargs -0 -P 4 -I {} \
    python pdf_extractor.py {} output/$(basename {} .pdf).json
```

### Practice 10.5: Monitoring and Logging

```bash
# Detailed logging
python pdf_extractor.py document.pdf output.json 2>&1 | tee extraction.log

# With timestamps
python pdf_extractor.py document.pdf output.json 2>&1 | \
    while IFS= read -r line; do 
        echo "$(date '+%Y-%m-%d %H:%M:%S') $line"
    done | tee -a extraction.log
```

### Practice 10.6: Data Backup

```bash
# Backup before processing
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_${DATE}.tar.gz output/

# Or use rsync for incremental backup
rsync -av --backup --backup-dir=backup_${DATE} output/ backup/current/
```

---

## Quick Reference Card

### Common Commands

```bash
# Basic extraction
python pdf_extractor.py input.pdf output.json

# With OCR
python pdf_extractor.py input.pdf output.json --ocr-backend easyocr

# To stdout
python pdf_extractor.py input.pdf

# Check backends
python pdf_extractor.py --list-backends

# Help
python pdf_extractor.py --help
```

### Environment Variables

```bash
export PDF_EXTRACTOR_OCR_BACKEND=easyocr  # Set default OCR backend
```

### Quick Analysis

```bash
# Count pages
python -c "import json; print(len(json.load(open('output.json'))))"

# Count images
python -c "import json; print(sum(len(p['images']) for p in json.load(open('output.json'))))"

# Count tables
python -c "import json; print(sum(len(p['tables']) for p in json.load(open('output.json'))))"
```

---

## Support and Resources

- **README:** See `README.md` for feature overview
- **Requirements:** See `requirements.txt` for dependencies
- **Schema:** See output examples in this guide
- **Validation:** See `AWS_DIAGRAM_ANALYSIS.md` for real-world testing

---

**End of Execution Guide**

*Last updated: November 26, 2025*


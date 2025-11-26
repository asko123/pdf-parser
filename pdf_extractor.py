#!/usr/bin/env python3
"""
PDF Content Extractor

Extracts structured content from PDF files including:
- Text content
- Tables with complex structures (merged cells, nested tables)
- Images with OCR text extraction and descriptions

Supports multiple OCR backends:
- none: No OCR (returns null for ocr_text) - no dependencies
- easyocr: Pure pip-installable OCR (no system dependencies)
- tesseract: Requires system Tesseract installation
"""

import argparse
import json
import io
import os
import sys
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image


OCR_BACKEND = os.environ.get("PDF_EXTRACTOR_OCR_BACKEND", "none")

_easyocr_reader = None
_tesseract_available = None
_easyocr_available = None


def _check_tesseract_available() -> bool:
    """Check if Tesseract is available on the system."""
    global _tesseract_available
    if _tesseract_available is not None:
        return _tesseract_available
    
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        _tesseract_available = True
    except Exception:
        _tesseract_available = False
    
    return _tesseract_available


def _check_easyocr_available() -> bool:
    """Check if EasyOCR is available."""
    global _easyocr_available
    if _easyocr_available is not None:
        return _easyocr_available
    
    try:
        import easyocr  # noqa: F401
        _easyocr_available = True
    except ImportError:
        _easyocr_available = False
    
    return _easyocr_available


def _get_easyocr_reader():
    """Get or create EasyOCR reader instance (lazy initialization)."""
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        print("Initializing EasyOCR (first run may download models)...", file=sys.stderr)
        _easyocr_reader = easyocr.Reader(['en'], gpu=False)
    return _easyocr_reader


def extract_text_from_page(pdf_page: pdfplumber.page.Page) -> str | None:
    """Extract all text content from a PDF page using pdfplumber."""
    text = pdf_page.extract_text()
    if text and text.strip():
        return text.strip()
    return None


def extract_tables_from_page(pdf_page: pdfplumber.page.Page, page_num: int) -> list[dict[str, Any]]:
    """
    Extract tables from a PDF page with support for complex structures.
    
    Returns a list of table dictionaries with structure including rows and merged cells.
    """
    tables = []
    
    try:
        extracted_tables = pdf_page.extract_tables()
        
        for table_idx, table_data in enumerate(extracted_tables):
            if not table_data:
                continue
            
            table_id = f"table_p{page_num}_t{table_idx + 1}"
            
            rows = []
            for row in table_data:
                processed_row = []
                for cell in row:
                    if cell is None:
                        processed_row.append("")
                    else:
                        processed_row.append(str(cell).strip())
                rows.append(processed_row)
            
            merged_cells = detect_merged_cells(table_data)
            
            table_dict = {
                "table_id": table_id,
                "structure": {
                    "rows": rows,
                    "merged_cells": merged_cells
                }
            }
            tables.append(table_dict)
    
    except Exception as e:
        print(f"Warning: Error extracting tables from page {page_num}: {e}", file=sys.stderr)
    
    return tables


def detect_merged_cells(table_data: list[list[Any]]) -> list[dict[str, int]]:
    """
    Detect merged cells in a table by analyzing cell patterns.
    
    Merged cells are detected by:
    1. Empty cells that follow non-empty cells (horizontal merge)
    2. Repeated values in consecutive rows (vertical merge)
    """
    merged_cells = []
    
    if not table_data or len(table_data) == 0:
        return merged_cells
    
    num_rows = len(table_data)
    num_cols = max(len(row) for row in table_data) if table_data else 0
    
    if num_cols == 0:
        return merged_cells
    
    processed = [[False] * num_cols for _ in range(num_rows)]
    
    for row_idx in range(num_rows):
        for col_idx in range(num_cols):
            if processed[row_idx][col_idx]:
                continue
            
            if col_idx >= len(table_data[row_idx]):
                continue
            
            cell_value = table_data[row_idx][col_idx]
            
            if cell_value is None or (isinstance(cell_value, str) and cell_value.strip() == ""):
                processed[row_idx][col_idx] = True
                continue
            
            colspan = 1
            for next_col in range(col_idx + 1, num_cols):
                if next_col >= len(table_data[row_idx]):
                    break
                next_value = table_data[row_idx][next_col]
                if next_value is None or (isinstance(next_value, str) and next_value.strip() == ""):
                    colspan += 1
                else:
                    break
            
            rowspan = 1
            for next_row in range(row_idx + 1, num_rows):
                if col_idx >= len(table_data[next_row]):
                    break
                next_value = table_data[next_row][col_idx]
                if next_value == cell_value:
                    rowspan += 1
                else:
                    break
            
            if rowspan > 1 or colspan > 1:
                merged_cells.append({
                    "row": row_idx,
                    "col": col_idx,
                    "rowspan": rowspan,
                    "colspan": colspan
                })
                
                for r in range(row_idx, row_idx + rowspan):
                    for c in range(col_idx, col_idx + colspan):
                        if r < num_rows and c < num_cols:
                            processed[r][c] = True
            else:
                processed[row_idx][col_idx] = True
    
    return merged_cells


def extract_images_from_page(
    fitz_doc: fitz.Document,
    page_num: int,
    ocr_backend: str = "none"
) -> list[dict[str, Any]]:
    """
    Extract images from a PDF page with OCR text extraction.
    
    Returns a list of image dictionaries with descriptions and OCR text.
    """
    images = []
    
    try:
        fitz_page = fitz_doc[page_num - 1]  # fitz uses 0-based indexing
        image_list = fitz_page.get_images(full=True)
        
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            image_id = f"image_p{page_num}_i{img_idx + 1}"
            
            try:
                base_image = fitz_doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                pil_image = Image.open(io.BytesIO(image_bytes))
                
                description = generate_image_description(pil_image, image_ext, img_idx + 1)
                
                ocr_text = extract_ocr_text(pil_image, backend=ocr_backend)
                
                image_dict = {
                    "image_id": image_id,
                    "description": description,
                    "ocr_text": ocr_text
                }
                images.append(image_dict)
                
            except Exception as e:
                print(f"Warning: Error processing image {img_idx + 1} on page {page_num}: {e}", file=sys.stderr)
                images.append({
                    "image_id": image_id,
                    "description": f"Image {img_idx + 1} (extraction failed)",
                    "ocr_text": None
                })
    
    except Exception as e:
        print(f"Warning: Error extracting images from page {page_num}: {e}", file=sys.stderr)
    
    return images


def generate_image_description(image: Image.Image, image_format: str, image_number: int) -> str:
    """
    Generate a descriptive context for an image.
    
    Analyzes image properties to provide meaningful description.
    """
    width, height = image.size
    mode = image.mode
    
    color_description = "color" if mode in ("RGB", "RGBA", "P") else "grayscale" if mode in ("L", "LA") else mode
    
    aspect_ratio = width / height if height > 0 else 1
    if aspect_ratio > 1.5:
        orientation = "wide/landscape"
    elif aspect_ratio < 0.67:
        orientation = "tall/portrait"
    else:
        orientation = "square-ish"
    
    size_category = "small" if width * height < 10000 else "medium" if width * height < 100000 else "large"
    
    description = (
        f"Image {image_number}: A {size_category} {color_description} {orientation} image "
        f"({width}x{height} pixels, {image_format.upper()} format)"
    )
    
    return description


def extract_ocr_text(image: Image.Image, backend: str = "none") -> str | None:
    """
    Extract text from an image using the specified OCR backend.
    
    Supported backends:
    - none: Returns None (no OCR)
    - easyocr: Uses EasyOCR (pip install easyocr)
    - tesseract: Uses Tesseract (requires system installation)
    
    Returns the extracted text or None if no text is found or OCR is disabled.
    """
    if backend == "none":
        return None
    
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    
    if backend == "easyocr":
        return _extract_ocr_easyocr(image)
    elif backend == "tesseract":
        return _extract_ocr_tesseract(image)
    else:
        print(f"Warning: Unknown OCR backend '{backend}', skipping OCR", file=sys.stderr)
        return None


def _extract_ocr_easyocr(image: Image.Image) -> str | None:
    """Extract text using EasyOCR."""
    if not _check_easyocr_available():
        print("Warning: EasyOCR not installed. Install with: pip install easyocr", file=sys.stderr)
        return None
    
    try:
        import numpy as np
        reader = _get_easyocr_reader()
        
        img_array = np.array(image)
        
        results = reader.readtext(img_array, detail=0)
        
        if results:
            text = " ".join(results).strip()
            return text if text else None
        return None
        
    except Exception as e:
        print(f"Warning: EasyOCR extraction failed: {e}", file=sys.stderr)
        return None


def _extract_ocr_tesseract(image: Image.Image) -> str | None:
    """Extract text using Tesseract."""
    if not _check_tesseract_available():
        print("Warning: Tesseract not available. Install with: sudo apt-get install tesseract-ocr", file=sys.stderr)
        return None
    
    try:
        import pytesseract
        
        ocr_result = pytesseract.image_to_string(image, lang='eng')
        
        cleaned_text = ocr_result.strip()
        
        if cleaned_text:
            return cleaned_text
        return None
        
    except Exception as e:
        print(f"Warning: Tesseract OCR extraction failed: {e}", file=sys.stderr)
        return None


def extract_pdf_content(pdf_path: str, ocr_backend: str = "none") -> list[dict[str, Any]]:
    """
    Main function to extract all content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        ocr_backend: OCR backend to use ('none', 'easyocr', 'tesseract')
    
    Returns a list of page dictionaries conforming to the output schema.
    """
    pdf_path_obj = Path(pdf_path)
    
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    results = []
    
    fitz_doc = fitz.open(str(pdf_path))
    
    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)
        
        for page_num in range(1, total_pages + 1):
            print(f"Processing page {page_num}/{total_pages}...", file=sys.stderr)
            
            plumber_page = pdf.pages[page_num - 1]
            
            text = extract_text_from_page(plumber_page)
            
            tables = extract_tables_from_page(plumber_page, page_num)
            
            images = extract_images_from_page(fitz_doc, page_num, ocr_backend=ocr_backend)
            
            page_result = {
                "page_number": page_num,
                "text": text,
                "tables": tables,
                "images": images
            }
            
            results.append(page_result)
    
    fitz_doc.close()
    
    return results


def validate_output(results: list[dict[str, Any]]) -> bool:
    """
    Validate that the output conforms to the expected schema.
    
    Returns True if valid, raises ValueError if invalid.
    """
    required_fields = ["page_number", "text", "tables", "images"]
    
    for page_idx, page in enumerate(results):
        page_keys = list(page.keys())
        if page_keys != required_fields:
            raise ValueError(
                f"Page {page_idx + 1}: Field order mismatch. "
                f"Expected {required_fields}, got {page_keys}"
            )
        
        if not isinstance(page["page_number"], int):
            raise ValueError(f"Page {page_idx + 1}: page_number must be an integer")
        
        if page["text"] is not None and not isinstance(page["text"], str):
            raise ValueError(f"Page {page_idx + 1}: text must be string or null")
        
        if not isinstance(page["tables"], list):
            raise ValueError(f"Page {page_idx + 1}: tables must be an array")
        
        for table_idx, table in enumerate(page["tables"]):
            if "table_id" not in table or not isinstance(table["table_id"], str):
                raise ValueError(f"Page {page_idx + 1}, Table {table_idx + 1}: invalid table_id")
            if "structure" not in table:
                raise ValueError(f"Page {page_idx + 1}, Table {table_idx + 1}: missing structure")
            if "rows" not in table["structure"] or not isinstance(table["structure"]["rows"], list):
                raise ValueError(f"Page {page_idx + 1}, Table {table_idx + 1}: invalid rows")
            if "merged_cells" not in table["structure"] or not isinstance(table["structure"]["merged_cells"], list):
                raise ValueError(f"Page {page_idx + 1}, Table {table_idx + 1}: invalid merged_cells")
        
        if not isinstance(page["images"], list):
            raise ValueError(f"Page {page_idx + 1}: images must be an array")
        
        for img_idx, img in enumerate(page["images"]):
            if "image_id" not in img or not isinstance(img["image_id"], str):
                raise ValueError(f"Page {page_idx + 1}, Image {img_idx + 1}: invalid image_id")
            if "description" not in img or not isinstance(img["description"], str):
                raise ValueError(f"Page {page_idx + 1}, Image {img_idx + 1}: invalid description")
            if "ocr_text" not in img:
                raise ValueError(f"Page {page_idx + 1}, Image {img_idx + 1}: missing ocr_text")
            if img["ocr_text"] is not None and not isinstance(img["ocr_text"], str):
                raise ValueError(f"Page {page_idx + 1}, Image {img_idx + 1}: ocr_text must be string or null")
    
    return True


def list_available_backends() -> dict[str, bool]:
    """List available OCR backends and their status."""
    return {
        "none": True,  # Always available
        "easyocr": _check_easyocr_available(),
        "tesseract": _check_tesseract_available(),
    }


def main():
    """Main entry point for the PDF extractor."""
    parser = argparse.ArgumentParser(
        description="Extract structured content from PDF files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
OCR Backends:
  none       No OCR - returns null for ocr_text (default, no dependencies)
  easyocr    Pure Python OCR - install with: pip install easyocr
  tesseract  System Tesseract - requires: sudo apt-get install tesseract-ocr

Environment Variables:
  PDF_EXTRACTOR_OCR_BACKEND  Default OCR backend (overridden by --ocr-backend)

Examples:
  python pdf_extractor.py document.pdf
  python pdf_extractor.py document.pdf output.json --ocr-backend easyocr
  PDF_EXTRACTOR_OCR_BACKEND=easyocr python pdf_extractor.py document.pdf
        """
    )
    
    parser.add_argument("pdf_file", nargs="?", help="Path to the PDF file to process")
    parser.add_argument("output_file", nargs="?", help="Path to save JSON output (default: stdout)")
    parser.add_argument(
        "--ocr-backend",
        choices=["none", "easyocr", "tesseract"],
        default=OCR_BACKEND,
        help=f"OCR backend to use (default: {OCR_BACKEND})"
    )
    parser.add_argument(
        "--list-backends",
        action="store_true",
        help="List available OCR backends and exit"
    )
    
    args = parser.parse_args()
    
    if args.list_backends:
        backends = list_available_backends()
        print("Available OCR backends:")
        for backend, available in backends.items():
            status = "available" if available else "not installed"
            print(f"  {backend}: {status}")
        sys.exit(0)
    
    if not args.pdf_file:
        parser.print_help()
        sys.exit(1)
    
    try:
        print(f"Extracting content from: {args.pdf_file}", file=sys.stderr)
        print(f"OCR backend: {args.ocr_backend}", file=sys.stderr)
        
        results = extract_pdf_content(args.pdf_file, ocr_backend=args.ocr_backend)
        
        print("Validating output schema...", file=sys.stderr)
        validate_output(results)
        print("Validation passed.", file=sys.stderr)
        
        json_output = json.dumps(results, indent=2, ensure_ascii=False)
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"Output saved to: {args.output_file}", file=sys.stderr)
        else:
            print(json_output)
        
        print(f"Successfully processed {len(results)} page(s).", file=sys.stderr)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

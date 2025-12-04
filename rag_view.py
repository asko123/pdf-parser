def build_rag_view(
    pages: List[Dict[str, Any]],
    document_path: str,
) -> Dict[str, Any]:
    """
    Create a RAG-friendly representation:
      - raw_text: concatenated text from all pages, annotated by page
      - tables: list of tables with page metadata

    Structure:
    {
      "raw_text": "...",
      "tables": [
        {
          "page_number": int,
          "table_id": "string",
          "markdown": "string"
        },
        ...
      ]
    }
    """
    raw_text_parts: List[str] = []
    tables_for_rag: List[Dict[str, Any]] = []

    for page in pages:
        page_num = page.get("page_number")
        page_text = (page.get("text") or "").strip()

        if page_text:
            # Include a simple page delimiter; helps recovery later
            raw_text_parts.append(f"[PAGE {page_num}]\n{page_text}")

        for tbl in page.get("tables", []) or []:
            tables_for_rag.append(
                {
                    "document_path": document_path,
                    "page_number": page_num,
                    "table_id": tbl.get("id"),
                    "markdown": tbl.get("markdown", ""),
                }
            )

    raw_text = "\n\n".join(raw_text_parts).strip()

    return {
        "raw_text": raw_text,
        "tables": tables_for_rag,
    }

def parse_pdf_with_gemini(
    pdf_path: str,
    max_pages: Optional[int] = None,
    for_rag: bool = False,
) -> Dict[str, Any]:
    """
    Parse a PDF into structured JSON using gemini-2.5-pro-vision.

    If for_rag=True, also include a 'rag' section with:
      - rag["raw_text"]
      - rag["tables"]
    """
    client = make_client()
    page_images = pdf_to_images(pdf_path)

    if max_pages is None:
        max_pages = len(page_images)
    max_pages = min(max_pages, len(page_images))

    pages: List[Dict[str, Any]] = []

    for idx in range(max_pages):
        page_num = idx + 1
        logging.info("Parsing page %s/%s", page_num, max_pages)
        page_img = page_images[idx]
        page_result = parse_page_with_gemini(client, page_img, page_num)
        pages.append(page_result)

    doc: Dict[str, Any] = {
        "document_path": pdf_path,
        "pages": pages,
    }

    if for_rag:
        doc["rag"] = build_rag_view(pages, pdf_path)

    return doc
def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Parse PDF text, tables, and images using gemini-2.5-pro-vision via GS AI."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file to parse.")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional limit on number of pages to process.",
    )
    parser.add_argument(
        "--for-rag",
        action="store_true",
        help="Include RAG-friendly 'raw_text' and 'tables' in the output.",
    )

    args = parser.parse_args()

    doc_result = parse_pdf_with_gemini(
        pdf_path=args.pdf_path,
        max_pages=args.max_pages,
        for_rag=args.for_rag,
    )

    if args.for_rag and "rag" in doc_result:
        print("\n=== RAG RAW TEXT ===\n")
        print(doc_result["rag"]["raw_text"])
        print("\n=== RAG TABLES JSON ===\n")
        print(json.dumps(doc_result["rag"]["tables"], indent=2))
        print("\n=== FULL PARSED DOCUMENT (for debugging) ===\n")
        pprint(doc_result)
    else:
        pprint(doc_result)


if __name__ == "__main__":
    main()

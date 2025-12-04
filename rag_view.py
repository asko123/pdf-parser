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

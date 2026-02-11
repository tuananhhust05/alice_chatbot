import os
from typing import List, Dict
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def extract_text_from_csv(file_path: str) -> str:
    """Extract text from CSV file, converting to readable, bounded format."""
    df = pd.read_csv(file_path)
    lines: List[str] = []
    lines.append(f"CSV file with {len(df)} rows and {len(df.columns)} columns.")
    lines.append(f"Columns: {', '.join(df.columns.tolist())}")
    lines.append("")
    lines.append("Data summary:")
    try:
        summary = df.describe(include="all").to_string()
        lines.append(summary)
    except Exception:
        # Fallback if describe fails (e.g. non-numeric only)
        lines.append("Summary not available.")
    lines.append("")
    lines.append("First 20 rows:")
    lines.append(df.head(20).to_string())

    if len(df) > 20:
        lines.append(f"\n... and {len(df) - 20} more rows (truncated for context).")

    return "\n".join(lines)


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from Word .docx file."""
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text_from_excel(file_path: str) -> str:
    """Extract text from Excel .xlsx file in a bounded, readable format."""
    # Use first sheet as primary context
    df = pd.read_excel(file_path)

    lines: List[str] = []
    lines.append(f"Excel file with {len(df)} rows and {len(df.columns)} columns.")
    lines.append(f"Columns: {', '.join(df.columns.tolist())}")
    lines.append("")
    lines.append("Data summary:")
    try:
        summary = df.describe(include="all").to_string()
        lines.append(summary)
    except Exception:
        lines.append("Summary not available.")
    lines.append("")
    lines.append("First 20 rows:")
    lines.append(df.head(20).to_string())

    if len(df) > 20:
        lines.append(f"\n... and {len(df) - 20} more rows (truncated for context).")

    return "\n".join(lines)


def build_tabular_preview(file_path: str, file_type: str, max_rows: int = 10) -> str | None:
    """
    Build a small markdown table preview for tabular files (CSV, Excel).
    Used for UI display, not full context.
    """
    try:
        if file_type == "csv":
            df = pd.read_csv(file_path)
        elif file_type in {"xlsx", "xls"}:
            df = pd.read_excel(file_path)
        else:
            return None

        if df.empty:
            return None

        head = df.head(max_rows)
        # Try to generate a markdown table (requires tabulate dependency)
        try:
            table_md = head.to_markdown(index=False)
        except Exception:
            # Fallback to plain text representation
            table_md = head.to_string(index=False)

        if len(df) > max_rows:
            table_md += f"\n\n... and {len(df) - max_rows} more rows."

        return table_md
    except Exception:
        return None


def extract_text(file_path: str, file_type: str) -> str:
    """Extract text from file based on type."""
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "txt":
        return extract_text_from_txt(file_path)
    elif file_type == "csv":
        return extract_text_from_csv(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type in {"xlsx", "xls"}:
        return extract_text_from_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
    """Split text into overlapping chunks."""
    chunks = []

    if len(text) <= chunk_size:
        chunks.append({
            "content": text,
            "metadata": "Chunk 1 of 1",
        })
        return chunks

    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            for sep in [". ", ".\n", "\n\n", "\n", " "]:
                last_sep = text[start:end].rfind(sep)
                if last_sep > chunk_size // 2:
                    end = start + last_sep + len(sep)
                    break

        chunk_content = text[start:end].strip()
        if chunk_content:
            chunks.append({
                "content": chunk_content,
                "metadata": f"Chunk {chunk_index + 1}",
            })
            chunk_index += 1

        start = end - overlap
        if start >= len(text):
            break

    return chunks

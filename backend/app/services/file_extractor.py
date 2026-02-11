"""
File text extraction utilities.
Supports: PDF, TXT, CSV, XLSX, DOCX with strict limits.

Token limits are set conservatively to stay within Groq's 12K TPM limit.
"""
import os
import re
import tempfile
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd


# ===== LIMITS =====
# Groq free tier: 12K tokens/minute
# Reserve ~3K for system prompt + history + response
MAX_FILE_SIZE_MB = 5            # Maximum file size in MB
MAX_TEXT_LENGTH = 20000         # Maximum extracted text length (chars)
MAX_PDF_PAGES = 20              # Maximum PDF pages to process
MAX_CSV_ROWS = 100              # Maximum CSV rows to read
MAX_EXCEL_ROWS = 100            # Maximum Excel rows to read  
MAX_EXCEL_SHEETS = 2            # Maximum Excel sheets to read


def compact_whitespace(text: str) -> str:
    """Remove excessive whitespace while preserving structure."""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines (3+) with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing spaces on each line
    text = re.sub(r' +\n', '\n', text)
    # Remove leading spaces on each line (except indentation)
    text = re.sub(r'\n +', '\n', text)
    return text.strip()


def df_to_compact_csv(df: pd.DataFrame) -> str:
    """Convert DataFrame to compact CSV format (less whitespace than to_string)."""
    # Fill NaN with empty string
    df = df.fillna('')
    
    # Convert all values to string and strip whitespace
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Use CSV format with | separator (more compact than to_string)
    lines = []
    
    # Header
    lines.append('|'.join(str(c).strip() for c in df.columns))
    lines.append('-' * min(len(lines[0]), 50))  # Short separator
    
    # Data rows
    for _, row in df.iterrows():
        row_str = '|'.join(str(v).strip()[:50] for v in row.values)  # Limit cell length
        lines.append(row_str)
    
    return '\n'.join(lines)


def extract_text_from_pdf(file_path: str) -> tuple[str, dict]:
    """Extract text from PDF file with page limit."""
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    pages_to_read = min(total_pages, MAX_PDF_PAGES)
    
    text = ""
    for i, page in enumerate(reader.pages[:pages_to_read]):
        page_text = page.extract_text()
        if page_text:
            # Compact the page text
            page_text = compact_whitespace(page_text)
            text += f"[Page {i+1}]\n{page_text}\n"
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
            break
    
    info = {
        "total_pages": total_pages,
        "pages_read": pages_to_read,
        "truncated": total_pages > MAX_PDF_PAGES or len(text) >= MAX_TEXT_LENGTH,
    }
    
    if total_pages > MAX_PDF_PAGES:
        text += f"\n[Truncated: {pages_to_read}/{total_pages} pages]"
    
    return compact_whitespace(text), info


def extract_text_from_txt(file_path: str) -> tuple[str, dict]:
    """Extract text from TXT file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    
    text = compact_whitespace(text)
    lines = text.count('\n') + 1
    info = {"lines": lines, "truncated": len(text) > MAX_TEXT_LENGTH}
    
    return text, info


def extract_text_from_csv(file_path: str) -> tuple[str, dict]:
    """Extract text from CSV file with row limit - compact format."""
    df = pd.read_csv(file_path, nrows=MAX_CSV_ROWS + 1)
    
    total_rows_approx = len(df)
    truncated = len(df) > MAX_CSV_ROWS
    if truncated:
        df = df.head(MAX_CSV_ROWS)
        try:
            with open(file_path, 'r') as f:
                total_rows_approx = sum(1 for _ in f) - 1
        except:
            pass
    
    # Build compact output
    header = f"CSV: {len(df)}rows x {len(df.columns)}cols"
    if truncated:
        header += f" (showing {MAX_CSV_ROWS}/{total_rows_approx})"
    
    # Compact table
    table = df_to_compact_csv(df)
    
    text = f"{header}\n{table}"
    
    info = {
        "rows": len(df),
        "columns": len(df.columns),
        "total_rows": total_rows_approx,
        "truncated": truncated,
    }
    
    return text, info


def extract_text_from_excel(file_path: str) -> tuple[str, dict]:
    """Extract text from Excel file with row/sheet limits - compact format."""
    xl = pd.ExcelFile(file_path)
    all_sheets = xl.sheet_names
    sheets_to_read = all_sheets[:MAX_EXCEL_SHEETS]
    
    parts = []
    total_rows = 0
    
    for sheet_name in sheets_to_read:
        df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=MAX_EXCEL_ROWS + 1)
        
        truncated = len(df) > MAX_EXCEL_ROWS
        if truncated:
            df = df.head(MAX_EXCEL_ROWS)
        
        # Compact header
        header = f"[{sheet_name}] {len(df)}rows x {len(df.columns)}cols"
        if truncated:
            header += f" (truncated)"
        
        # Compact table
        table = df_to_compact_csv(df)
        
        parts.append(f"{header}\n{table}")
        total_rows += len(df)
    
    if len(all_sheets) > MAX_EXCEL_SHEETS:
        parts.append(f"[+{len(all_sheets) - MAX_EXCEL_SHEETS} more sheets]")
    
    text = '\n'.join(parts)
    
    info = {
        "total_sheets": len(all_sheets),
        "sheets_read": len(sheets_to_read),
        "total_rows": total_rows,
        "truncated_sheets": len(all_sheets) > MAX_EXCEL_SHEETS,
    }
    
    return text, info


def extract_text_from_docx(file_path: str) -> tuple[str, dict]:
    """Extract text from Word .docx file."""
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)  # Single newline instead of double
    text = compact_whitespace(text)
    
    info = {"paragraphs": len(paragraphs), "truncated": len(text) > MAX_TEXT_LENGTH}
    
    return text, info


def extract_text(file_path: str, file_type: str) -> tuple[str, dict]:
    """Extract text from file based on type. Returns (text, info)."""
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


async def extract_from_upload(content: bytes, filename: str, file_type: str) -> dict:
    """
    Extract text from uploaded file content.
    Returns extraction result with text and metadata.
    """
    suffix = f".{file_type}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        text, info = extract_text(tmp_path, file_type)
        
        # Apply text length limit
        text_truncated = False
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH] + "\n[Truncated]"
            text_truncated = True
        
        return {
            "text": text,
            "original_name": filename,
            "file_type": file_type,
            "file_size": len(content),
            "text_length": len(text),
            "text_truncated": text_truncated,
            "extraction_info": info,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

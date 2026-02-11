from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel

from app.dependencies import get_current_user_dep
from app.services.file_extractor import extract_from_upload, MAX_FILE_SIZE_MB
from app.security import validate_filename, log_security_event, get_client_ip

router = APIRouter(prefix="/api/files", tags=["files"])

# Supported file types
ALLOWED_EXTENSIONS = {"pdf", "txt", "csv", "docx", "xlsx"}


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


class FileExtractResponse(BaseModel):
    """Response from file text extraction."""
    text: str
    original_name: str
    file_type: str
    file_size: int
    text_length: int
    text_truncated: bool = False


@router.post("/extract", response_model=FileExtractResponse)
async def extract_file_content(
    raw_request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user_dep),
):
    """
    Upload file and extract text content immediately.
    Supports: PDF, TXT, CSV, DOCX, XLSX
    
    Returns extracted text. Content is embedded in message when sent.
    """
    user_id = user["email"]
    client_ip = get_client_ip(raw_request)
    
    # ===== SECURITY: Filename Validation =====
    is_valid, error_msg = validate_filename(file.filename or "")
    if not is_valid:
        log_security_event(
            event_type="invalid_filename_blocked",
            client_ip=client_ip,
            user_id=user_id,
            details={"error": error_msg, "filename": file.filename},
            severity="warning"
        )
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Validate extension
    file_ext = get_file_extension(file.filename or "")
    if file_ext not in ALLOWED_EXTENSIONS:
        log_security_event(
            event_type="disallowed_file_type",
            client_ip=client_ip,
            user_id=user_id,
            details={"file_type": file_ext, "filename": file.filename},
            severity="info"
        )
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not supported. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    
    # Read content
    content = await file.read()
    file_size = len(content)
    
    # Check size limit
    max_size = MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {MAX_FILE_SIZE_MB}MB, your file: {file_size / 1024 / 1024:.1f}MB",
        )
    
    # Extract text
    try:
        result = await extract_from_upload(content, file.filename or "file", file_ext)
        return FileExtractResponse(
            text=result["text"],
            original_name=result["original_name"],
            file_type=result["file_type"],
            file_size=result["file_size"],
            text_length=result["text_length"],
            text_truncated=result["text_truncated"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")


@router.get("/limits")
async def get_file_limits():
    """Get current file extraction limits."""
    from app.services.file_extractor import (
        MAX_FILE_SIZE_MB, MAX_TEXT_LENGTH, MAX_PDF_PAGES,
        MAX_CSV_ROWS, MAX_EXCEL_ROWS, MAX_EXCEL_SHEETS
    )
    return {
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "max_text_length": MAX_TEXT_LENGTH,
        "max_pdf_pages": MAX_PDF_PAGES,
        "max_csv_rows": MAX_CSV_ROWS,
        "max_excel_rows": MAX_EXCEL_ROWS,
        "max_excel_sheets": MAX_EXCEL_SHEETS,
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
    }

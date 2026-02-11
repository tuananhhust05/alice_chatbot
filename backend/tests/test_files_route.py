"""
Tests for files routes.
"""
import pytest
from unittest.mock import patch, AsyncMock
from io import BytesIO

from app.routes.files import get_file_extension, ALLOWED_EXTENSIONS


class TestGetFileExtension:
    """Tests for get_file_extension helper function."""
    
    def test_extracts_pdf_extension(self):
        assert get_file_extension("document.pdf") == "pdf"
    
    def test_extracts_txt_extension(self):
        assert get_file_extension("notes.txt") == "txt"
    
    def test_extracts_csv_extension(self):
        assert get_file_extension("data.csv") == "csv"
    
    def test_extracts_docx_extension(self):
        assert get_file_extension("report.docx") == "docx"
    
    def test_extracts_xlsx_extension(self):
        assert get_file_extension("spreadsheet.xlsx") == "xlsx"
    
    def test_handles_multiple_dots(self):
        assert get_file_extension("file.backup.pdf") == "pdf"
    
    def test_returns_lowercase(self):
        assert get_file_extension("FILE.PDF") == "pdf"
        assert get_file_extension("Data.CSV") == "csv"
    
    def test_returns_empty_for_no_extension(self):
        assert get_file_extension("filename") == ""
    
    def test_handles_empty_string(self):
        assert get_file_extension("") == ""
    
    def test_handles_dot_only(self):
        result = get_file_extension("file.")
        assert result == ""


class TestAllowedExtensions:
    """Tests for ALLOWED_EXTENSIONS constant."""
    
    def test_includes_pdf(self):
        assert "pdf" in ALLOWED_EXTENSIONS
    
    def test_includes_txt(self):
        assert "txt" in ALLOWED_EXTENSIONS
    
    def test_includes_csv(self):
        assert "csv" in ALLOWED_EXTENSIONS
    
    def test_includes_docx(self):
        assert "docx" in ALLOWED_EXTENSIONS
    
    def test_includes_xlsx(self):
        assert "xlsx" in ALLOWED_EXTENSIONS
    
    def test_does_not_include_exe(self):
        assert "exe" not in ALLOWED_EXTENSIONS
    
    def test_does_not_include_js(self):
        assert "js" not in ALLOWED_EXTENSIONS
    
    def test_is_set(self):
        assert isinstance(ALLOWED_EXTENSIONS, set)


class TestExtractFileContentEndpoint:
    """Tests for /api/files/extract endpoint."""
    
    @pytest.mark.asyncio
    async def test_rejects_unsupported_file_type(self, authed_async_client):
        # Create fake file with unsupported extension
        files = {"file": ("test.exe", b"malicious content", "application/octet-stream")}
        
        response = await authed_async_client.post("/api/files/extract", files=files)
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_extracts_txt_file(self, authed_async_client):
        # Mock the extract_from_upload function
        with patch("app.routes.files.extract_from_upload", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = {
                "text": "Hello, World!",
                "original_name": "test.txt",
                "file_type": "txt",
                "file_size": 13,
                "text_length": 13,
                "text_truncated": False,
            }
            
            files = {"file": ("test.txt", b"Hello, World!", "text/plain")}
            response = await authed_async_client.post("/api/files/extract", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Hello, World!"
        assert data["original_name"] == "test.txt"
        assert data["file_type"] == "txt"
    
    @pytest.mark.asyncio
    async def test_returns_extraction_metadata(self, authed_async_client):
        with patch("app.routes.files.extract_from_upload", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = {
                "text": "CSV content",
                "original_name": "data.csv",
                "file_type": "csv",
                "file_size": 100,
                "text_length": 11,
                "text_truncated": False,
            }
            
            files = {"file": ("data.csv", b"a,b\n1,2", "text/csv")}
            response = await authed_async_client.post("/api/files/extract", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "original_name" in data
        assert "file_type" in data
        assert "file_size" in data
        assert "text_length" in data
        assert "text_truncated" in data


class TestFileLimitsEndpoint:
    """Tests for /api/files/limits endpoint."""
    
    @pytest.mark.asyncio
    async def test_returns_limits(self, async_client):
        """Test that limits endpoint returns expected fields (no auth required)."""
        response = await async_client.get("/api/files/limits")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "max_file_size_mb" in data
        assert "max_text_length" in data
        assert "max_pdf_pages" in data
        assert "max_csv_rows" in data
        assert "max_excel_rows" in data
        assert "max_excel_sheets" in data
        assert "allowed_extensions" in data
    
    @pytest.mark.asyncio
    async def test_allowed_extensions_match(self, async_client):
        """Test that returned extensions match the constant."""
        response = await async_client.get("/api/files/limits")
        data = response.json()
        
        extensions = set(data["allowed_extensions"])
        assert extensions == ALLOWED_EXTENSIONS

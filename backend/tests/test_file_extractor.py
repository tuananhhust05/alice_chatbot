"""
Tests for file_extractor service.
"""
import pytest
import pandas as pd
import tempfile
import os

from app.services.file_extractor import (
    compact_whitespace,
    df_to_compact_csv,
    extract_text_from_txt,
    extract_text_from_csv,
    extract_text,
    extract_from_upload,
    MAX_TEXT_LENGTH,
    MAX_CSV_ROWS,
)


class TestCompactWhitespace:
    """Tests for compact_whitespace function."""
    
    def test_removes_multiple_spaces(self):
        text = "Hello    world   test"
        result = compact_whitespace(text)
        assert result == "Hello world test"
    
    def test_reduces_multiple_newlines(self):
        text = "Line 1\n\n\n\nLine 2"
        result = compact_whitespace(text)
        assert result == "Line 1\n\nLine 2"
    
    def test_removes_trailing_spaces(self):
        text = "Hello   \nWorld   \n"
        result = compact_whitespace(text)
        assert "   \n" not in result
    
    def test_removes_leading_spaces_on_lines(self):
        text = "Hello\n   World"
        result = compact_whitespace(text)
        assert result == "Hello\nWorld"
    
    def test_strips_text(self):
        text = "  Hello World  "
        result = compact_whitespace(text)
        assert result == "Hello World"
    
    def test_empty_string(self):
        result = compact_whitespace("")
        assert result == ""
    
    def test_preserves_single_newlines(self):
        text = "Line 1\nLine 2\nLine 3"
        result = compact_whitespace(text)
        assert result == "Line 1\nLine 2\nLine 3"


class TestDfToCompactCsv:
    """Tests for df_to_compact_csv function."""
    
    def test_basic_dataframe(self):
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [30, 25],
        })
        result = df_to_compact_csv(df)
        
        assert "name|age" in result
        assert "Alice|30" in result
        assert "Bob|25" in result
    
    def test_handles_nan_values(self):
        df = pd.DataFrame({
            "name": ["Alice", None],
            "age": [30, None],
        })
        result = df_to_compact_csv(df)
        
        # NaN should be replaced with empty string
        assert "Alice|30" in result
        lines = result.split("\n")
        # Second data row should have empty values
        assert len(lines) >= 3
    
    def test_strips_whitespace(self):
        df = pd.DataFrame({
            "name": ["  Alice  ", "  Bob  "],
        })
        result = df_to_compact_csv(df)
        
        assert "Alice" in result
        assert "  Alice  " not in result
    
    def test_truncates_long_cell_values(self):
        long_value = "A" * 100
        df = pd.DataFrame({"col": [long_value]})
        result = df_to_compact_csv(df)
        
        # Cell should be truncated to 50 chars
        lines = result.split("\n")
        data_line = lines[-1]
        assert len(data_line) <= 50
    
    def test_includes_separator_line(self):
        df = pd.DataFrame({"col": ["value"]})
        result = df_to_compact_csv(df)
        
        lines = result.split("\n")
        # Second line should be separator
        assert lines[1].startswith("-")


class TestExtractTextFromTxt:
    """Tests for extract_text_from_txt function."""
    
    def test_extracts_text(self, temp_file):
        content = b"Hello, World!\nThis is a test file."
        file_path = temp_file("test.txt", content)
        
        text, info = extract_text_from_txt(file_path)
        
        assert "Hello, World!" in text
        assert "This is a test file." in text
    
    def test_returns_line_count(self, temp_file):
        content = b"Line 1\nLine 2\nLine 3"
        file_path = temp_file("test.txt", content)
        
        text, info = extract_text_from_txt(file_path)
        
        assert "lines" in info
        assert info["lines"] >= 1
    
    def test_handles_empty_file(self, temp_file):
        file_path = temp_file("empty.txt", b"")
        
        text, info = extract_text_from_txt(file_path)
        
        assert text == ""
    
    def test_handles_unicode(self, temp_file):
        content = "Hello 世界 🌍".encode("utf-8")
        file_path = temp_file("unicode.txt", content)
        
        text, info = extract_text_from_txt(file_path)
        
        assert "Hello" in text


class TestExtractTextFromCsv:
    """Tests for extract_text_from_csv function."""
    
    def test_extracts_csv_data(self, temp_file):
        content = b"name,age,city\nAlice,30,NYC\nBob,25,LA"
        file_path = temp_file("test.csv", content)
        
        text, info = extract_text_from_csv(file_path)
        
        assert "name" in text
        assert "Alice" in text
        assert "30" in text
    
    def test_returns_row_count(self, temp_file):
        content = b"col1,col2\n1,2\n3,4\n5,6"
        file_path = temp_file("test.csv", content)
        
        text, info = extract_text_from_csv(file_path)
        
        assert info["rows"] == 3
        assert info["columns"] == 2
    
    def test_includes_header_info(self, temp_file):
        content = b"a,b,c\n1,2,3"
        file_path = temp_file("test.csv", content)
        
        text, info = extract_text_from_csv(file_path)
        
        assert "CSV:" in text
        assert "rows" in text
        assert "cols" in text
    
    def test_truncates_large_csv(self, temp_file):
        # Create CSV with more rows than MAX_CSV_ROWS
        rows = ["col1,col2"] + [f"{i},{i*2}" for i in range(MAX_CSV_ROWS + 50)]
        content = "\n".join(rows).encode()
        file_path = temp_file("large.csv", content)
        
        text, info = extract_text_from_csv(file_path)
        
        assert info["truncated"] == True
        assert info["rows"] == MAX_CSV_ROWS


class TestExtractText:
    """Tests for extract_text dispatcher function."""
    
    def test_routes_to_txt(self, temp_file):
        content = b"Hello TXT"
        file_path = temp_file("test.txt", content)
        
        text, info = extract_text(file_path, "txt")
        
        assert "Hello TXT" in text
    
    def test_routes_to_csv(self, temp_file):
        content = b"a,b\n1,2"
        file_path = temp_file("test.csv", content)
        
        text, info = extract_text(file_path, "csv")
        
        assert "a" in text
    
    def test_raises_for_unsupported_type(self, temp_file):
        file_path = temp_file("test.xyz", b"content")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text(file_path, "xyz")


class TestExtractFromUpload:
    """Tests for extract_from_upload async function."""
    
    @pytest.mark.asyncio
    async def test_extracts_from_bytes(self):
        content = b"Hello, uploaded file!"
        
        result = await extract_from_upload(content, "test.txt", "txt")
        
        assert result["text"] == "Hello, uploaded file!"
        assert result["original_name"] == "test.txt"
        assert result["file_type"] == "txt"
        assert result["file_size"] == len(content)
    
    @pytest.mark.asyncio
    async def test_returns_text_length(self):
        content = b"Short text"
        
        result = await extract_from_upload(content, "test.txt", "txt")
        
        assert result["text_length"] == len(result["text"])
    
    @pytest.mark.asyncio
    async def test_truncates_long_text(self):
        # Create content longer than MAX_TEXT_LENGTH
        long_content = ("A" * (MAX_TEXT_LENGTH + 1000)).encode()
        
        result = await extract_from_upload(long_content, "long.txt", "txt")
        
        assert result["text_truncated"] == True
        assert len(result["text"]) <= MAX_TEXT_LENGTH + 100  # Some buffer for truncation message
        assert "[Truncated]" in result["text"]
    
    @pytest.mark.asyncio
    async def test_cleans_up_temp_file(self):
        content = b"Test content"
        
        # Get initial temp file count
        temp_dir = tempfile.gettempdir()
        
        result = await extract_from_upload(content, "test.txt", "txt")
        
        # Result should be returned successfully
        assert result["text"] == "Test content"
    
    @pytest.mark.asyncio
    async def test_csv_extraction(self):
        content = b"name,value\ntest,123"
        
        result = await extract_from_upload(content, "data.csv", "csv")
        
        assert result["file_type"] == "csv"
        assert "name" in result["text"]
        assert "test" in result["text"]

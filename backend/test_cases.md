# Backend Unit Tests

Documentation of unit tests coverage for the Backend service.

## Test Files Overview

| File | Tests | Description |
|------|-------|-------------|
| `test_auth.py` | 9 | Authentication & JWT token handling |
| `test_chat_route.py` | 10 | Chat API endpoints |
| `test_file_extractor.py` | 35+ | File text extraction utilities |
| `test_files_route.py` | 15 | File upload API endpoints |
| `test_kafka_producer.py` | 9 | Kafka message publishing |
| `test_models.py` | 22 | Pydantic model validation |
| `test_redis_client.py` | 7 | Redis caching operations |
| `test_security.py` | 40+ | Security utilities & validation |

---

## 1. Authentication (`test_auth.py`)

### Create Access Token
- `test_creates_valid_jwt` - Creates valid JWT token
- `test_token_contains_email` - Token contains user email claim
- `test_token_has_expiration` - Token has expiration time

### Get Current User
- `test_returns_user_for_valid_token` - Returns user for valid token
- `test_returns_none_for_invalid_token` - Returns None for invalid token
- `test_returns_none_for_expired_token` - Returns None for expired token
- `test_returns_none_when_user_not_found` - Returns None when user not in DB

### Get or Create User
- `test_returns_existing_user` - Returns existing user from DB
- `test_creates_new_user` - Creates new user if not exists

---

## 2. Chat Routes (`test_chat_route.py`)

### POST /api/chat/send
- `test_creates_new_conversation` - Creates new conversation when no ID provided
- `test_uses_display_content_for_title` - Uses display_content for conversation title
- `test_appends_to_existing_conversation` - Appends message to existing conversation
- `test_returns_404_for_nonexistent_conversation` - Returns 404 for invalid conversation ID

### GET /api/chat/conversations
- `test_returns_conversations_list` - Returns list of user's conversations
- `test_returns_empty_list_when_no_conversations` - Returns empty list when no conversations

### GET /api/chat/conversations/{id}
- `test_returns_conversation_detail` - Returns full conversation with messages
- `test_returns_404_for_nonexistent` - Returns 404 for non-existent conversation

### DELETE /api/chat/conversations/{id}
- `test_deletes_conversation` - Deletes conversation and returns success
- `test_returns_404_when_not_found` - Returns 404 when conversation not found

---

## 3. File Extractor (`test_file_extractor.py`)

### Compact Whitespace
- `test_removes_multiple_spaces` - Removes multiple consecutive spaces
- `test_reduces_multiple_newlines` - Reduces multiple newlines to single
- `test_removes_trailing_spaces` - Removes trailing spaces from lines
- `test_removes_leading_spaces_on_lines` - Removes leading spaces from lines

### Extract Text
- `test_extracts_txt_content` - Extracts text from TXT files
- `test_extracts_csv_content` - Extracts text from CSV files
- `test_extracts_pdf_content` - Extracts text from PDF files
- `test_extracts_docx_content` - Extracts text from DOCX files
- `test_extracts_xlsx_content` - Extracts text from XLSX files

### Text Truncation
- `test_truncates_long_text` - Truncates text exceeding max length
- `test_preserves_short_text` - Preserves text under max length

### CSV Handling
- `test_limits_csv_rows` - Limits number of CSV rows extracted
- `test_handles_csv_with_headers` - Preserves CSV headers

### Excel Handling
- `test_limits_excel_rows` - Limits number of Excel rows
- `test_limits_excel_sheets` - Limits number of Excel sheets
- `test_includes_sheet_names` - Includes sheet names in output

### PDF Handling
- `test_limits_pdf_pages` - Limits number of PDF pages extracted
- `test_handles_empty_pdf` - Handles empty PDF files

### Error Handling
- `test_raises_for_unsupported_type` - Raises error for unsupported file types
- `test_handles_corrupted_file` - Handles corrupted files gracefully

---

## 4. Files Routes (`test_files_route.py`)

### Helper Functions
- `test_extracts_pdf_extension` - Extracts 'pdf' from filename
- `test_extracts_txt_extension` - Extracts 'txt' from filename
- `test_extracts_csv_extension` - Extracts 'csv' from filename
- `test_extracts_docx_extension` - Extracts 'docx' from filename
- `test_extracts_xlsx_extension` - Extracts 'xlsx' from filename
- `test_handles_multiple_dots` - Handles filenames with multiple dots
- `test_returns_lowercase` - Returns lowercase extension
- `test_returns_empty_for_no_extension` - Returns empty for no extension
- `test_handles_empty_string` - Handles empty filename
- `test_handles_dot_only` - Handles filename ending with dot

### Allowed Extensions
- `test_includes_pdf` - PDF in allowed extensions
- `test_includes_txt` - TXT in allowed extensions
- `test_includes_csv` - CSV in allowed extensions
- `test_includes_docx` - DOCX in allowed extensions
- `test_includes_xlsx` - XLSX in allowed extensions
- `test_does_not_include_exe` - EXE not in allowed extensions
- `test_does_not_include_js` - JS not in allowed extensions
- `test_is_set` - ALLOWED_EXTENSIONS is a set

### POST /api/files/extract
- `test_rejects_unsupported_file_type` - Returns 400 for unsupported types
- `test_extracts_txt_file` - Extracts text from uploaded TXT file
- `test_returns_extraction_metadata` - Returns file metadata with extraction

### GET /api/files/limits
- `test_returns_limits` - Returns file extraction limits (no auth required)
- `test_allowed_extensions_match` - Returned extensions match constant

---

## 5. Kafka Producer (`test_kafka_producer.py`)

### Publish Chat Request
- `test_publishes_message_with_request_id` - Publishes with request_id included
- `test_includes_all_data_fields` - Includes all data fields in message

### Publish File Request
- `test_publishes_to_file_topic` - Publishes to file_requests topic

### Publish RAGdata Request
- `test_publishes_to_ragdata_topic` - Publishes to ragdata_requests topic

### Publish RAGdata Delete
- `test_publishes_delete_action` - Publishes delete action for file

### Connection Management
- `test_retries_on_failure` - Retries connection on failure
- `test_stops_producer` - Stops producer properly
- `test_handles_none_producer` - Handles None producer gracefully

---

## 6. Pydantic Models (`test_models.py`)

### Message Model
- `test_creates_valid_message` - Creates message with role and content
- `test_accepts_user_role` - Accepts 'user' role
- `test_accepts_assistant_role` - Accepts 'assistant' role
- `test_requires_role` - Role is required
- `test_requires_content` - Content is required
- `test_accepts_custom_timestamp` - Accepts custom timestamp
- `test_default_timestamp_is_now` - Default timestamp is current time

### ChatRequest Model
- `test_creates_with_message_only` - Creates with just message
- `test_accepts_all_fields` - Accepts message, display_content, conversation_id
- `test_requires_message` - Message is required
- `test_allows_empty_message` - Empty message string is valid

### ChatSendResponse Model
- `test_creates_valid_response` - Creates with request_id and conversation_id
- `test_requires_both_fields` - Both fields are required

### StreamResponse Model
- `test_creates_processing_response` - Creates processing status response
- `test_creates_completed_response` - Creates completed status with reply
- `test_creates_error_response` - Creates error status with error message
- `test_default_finished_is_zero` - Default finished is 0

### ConversationListItem Model
- `test_creates_valid_item` - Creates conversation list item
- `test_default_message_count` - Default message_count is 0

### ConversationDetail Model
- `test_creates_with_messages` - Creates with message list
- `test_default_empty_file_ids` - Default file_ids is empty list
- `test_accepts_file_ids` - Accepts file_ids list

---

## 7. Redis Client (`test_redis_client.py`)

### Get Result
- `test_returns_parsed_result` - Returns parsed JSON result
- `test_returns_none_when_not_found` - Returns None for missing key
- `test_uses_correct_key_prefix` - Uses 'result:' key prefix

### Delete Result
- `test_deletes_with_correct_key` - Deletes with correct key

### Connection Management
- `test_connects_and_pings` - Connects and pings Redis
- `test_closes_connection` - Closes connection properly
- `test_handles_none_client` - Handles None client gracefully

---

## 8. Security (`test_security.py`)

### Input Validation
- `test_rejects_empty_message` - Rejects empty messages
- `test_rejects_whitespace_only` - Rejects whitespace-only messages
- `test_accepts_valid_message` - Accepts valid messages
- `test_rejects_too_long_message` - Rejects messages exceeding max length
- `test_rejects_null_bytes` - Rejects messages with null bytes
- `test_accepts_unicode` - Accepts valid unicode characters

### Filename Validation
- `test_rejects_path_traversal` - Rejects '../' path traversal
- `test_rejects_absolute_path` - Rejects absolute paths
- `test_rejects_null_bytes_in_filename` - Rejects null bytes
- `test_accepts_valid_filename` - Accepts valid filenames
- `test_rejects_double_extension` - Rejects suspicious double extensions
- `test_rejects_empty_filename` - Rejects empty filename
- `test_rejects_too_long_filename` - Rejects overly long filenames

### Rate Limiting
- `test_rate_limit_key_generation` - Generates correct rate limit keys
- `test_rate_limit_check` - Checks rate limit correctly
- `test_rate_limit_increment` - Increments rate limit counter

### Security Headers
- `test_returns_security_headers` - Returns recommended security headers
- `test_includes_content_type_options` - Includes X-Content-Type-Options
- `test_includes_frame_options` - Includes X-Frame-Options
- `test_includes_xss_protection` - Includes X-XSS-Protection

### Client IP Detection
- `test_extracts_from_x_forwarded_for` - Extracts IP from X-Forwarded-For
- `test_extracts_from_x_real_ip` - Extracts IP from X-Real-IP
- `test_falls_back_to_client_host` - Falls back to request.client.host
- `test_handles_multiple_forwarded_ips` - Handles comma-separated IPs
- `test_handles_missing_client` - Handles missing client info

### Security Event Logging
- `test_logs_security_event` - Logs security events
- `test_includes_timestamp` - Includes timestamp in logs
- `test_includes_severity` - Includes severity level

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test class
pytest tests/test_security.py::TestInputValidation

# Run with verbose output
pytest -v

# Run only async tests
pytest -m asyncio
```

## Test Configuration

See `pytest.ini` for test configuration:
- Test paths: `tests/`
- Async mode: `auto`
- Output: `-v --tb=short`

## Test Fixtures

Common fixtures available in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `mock_db` | Mock MongoDB database |
| `mock_user` | Mock authenticated user |
| `mock_kafka_producer` | Mock Kafka producer |
| `mock_redis` | Mock Redis client |
| `app` | FastAPI test app |
| `client` | Sync test client |
| `async_client` | Async test client |
| `authed_async_client` | Async client with auth bypass |
| `auth_override` | Auth dependency override |
| `sample_txt_content` | Sample TXT file content |
| `sample_csv_content` | Sample CSV file content |
| `temp_file` | Helper to create temp files |

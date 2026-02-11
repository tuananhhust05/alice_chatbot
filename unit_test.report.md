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


## Result ( run pytest inside backend container)
root@1a8f9b51f719:/app# pytest 
=============================================================== test session starts ===============================================================
platform linux -- Python 3.11.14, pytest-8.0.2, pluggy-1.6.0 -- /usr/local/bin/python3.11
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.12.1, asyncio-0.23.5, cov-4.1.0
asyncio: mode=Mode.AUTO
collected 131 items                                                                                                                               

tests/test_auth.py::TestCreateAccessToken::test_creates_valid_jwt PASSED                                                                    [  0%]
tests/test_auth.py::TestCreateAccessToken::test_token_contains_email PASSED                                                                 [  1%] 
tests/test_auth.py::TestCreateAccessToken::test_token_has_expiration PASSED                                                                 [  2%] 
tests/test_auth.py::TestGetCurrentUser::test_returns_user_for_valid_token PASSED                                                            [  3%]
tests/test_auth.py::TestGetCurrentUser::test_returns_none_for_invalid_token PASSED                                                          [  3%] 
tests/test_auth.py::TestGetCurrentUser::test_returns_none_for_expired_token PASSED                                                          [  4%] 
tests/test_auth.py::TestGetCurrentUser::test_returns_none_when_user_not_found PASSED                                                        [  5%]
tests/test_auth.py::TestGetOrCreateUser::test_returns_existing_user PASSED                                                                  [  6%]
tests/test_auth.py::TestGetOrCreateUser::test_creates_new_user PASSED                                                                       [  6%]
tests/test_chat_route.py::TestSendMessageEndpoint::test_creates_new_conversation PASSED                                                     [  7%]
tests/test_chat_route.py::TestSendMessageEndpoint::test_uses_display_content_for_title PASSED                                               [  8%]
tests/test_chat_route.py::TestSendMessageEndpoint::test_appends_to_existing_conversation PASSED                                             [  9%]
tests/test_chat_route.py::TestSendMessageEndpoint::test_returns_404_for_nonexistent_conversation PASSED                                     [  9%] 
tests/test_chat_route.py::TestListConversationsEndpoint::test_returns_conversations_list PASSED                                             [ 10%] 
tests/test_chat_route.py::TestListConversationsEndpoint::test_returns_empty_list_when_no_conversations PASSED                               [ 11%]
tests/test_chat_route.py::TestGetConversationEndpoint::test_returns_conversation_detail PASSED                                              [ 12%]
tests/test_chat_route.py::TestGetConversationEndpoint::test_returns_404_for_nonexistent PASSED                                              [ 12%]
tests/test_chat_route.py::TestDeleteConversationEndpoint::test_deletes_conversation PASSED                                                  [ 13%] 
tests/test_chat_route.py::TestDeleteConversationEndpoint::test_returns_404_when_not_found PASSED                                            [ 14%] 
tests/test_file_extractor.py::TestCompactWhitespace::test_removes_multiple_spaces PASSED                                                    [ 15%] 
tests/test_file_extractor.py::TestCompactWhitespace::test_reduces_multiple_newlines PASSED                                                  [ 16%] 
tests/test_file_extractor.py::TestCompactWhitespace::test_removes_trailing_spaces PASSED                                                    [ 16%] 
tests/test_file_extractor.py::TestCompactWhitespace::test_removes_leading_spaces_on_lines PASSED                                            [ 17%] 
tests/test_file_extractor.py::TestCompactWhitespace::test_strips_text PASSED                                                                [ 18%] 
tests/test_file_extractor.py::TestCompactWhitespace::test_empty_string PASSED                                                               [ 19%] 
tests/test_file_extractor.py::TestCompactWhitespace::test_preserves_single_newlines PASSED                                                  [ 19%] 
tests/test_file_extractor.py::TestDfToCompactCsv::test_basic_dataframe PASSED                                                               [ 20%]
tests/test_file_extractor.py::TestDfToCompactCsv::test_handles_nan_values PASSED                                                            [ 21%] 
tests/test_file_extractor.py::TestDfToCompactCsv::test_strips_whitespace PASSED                                                             [ 22%] 
tests/test_file_extractor.py::TestDfToCompactCsv::test_truncates_long_cell_values PASSED                                                    [ 22%] 
tests/test_file_extractor.py::TestDfToCompactCsv::test_includes_separator_line PASSED                                                       [ 23%] 
tests/test_file_extractor.py::TestExtractTextFromTxt::test_extracts_text PASSED                                                             [ 24%]
tests/test_file_extractor.py::TestExtractTextFromTxt::test_returns_line_count PASSED                                                        [ 25%] 
tests/test_file_extractor.py::TestExtractTextFromTxt::test_handles_empty_file PASSED                                                        [ 25%] 
tests/test_file_extractor.py::TestExtractTextFromTxt::test_handles_unicode PASSED                                                           [ 26%] 
tests/test_file_extractor.py::TestExtractTextFromCsv::test_extracts_csv_data PASSED                                                         [ 27%]
tests/test_file_extractor.py::TestExtractTextFromCsv::test_returns_row_count PASSED                                                         [ 28%]
tests/test_file_extractor.py::TestExtractTextFromCsv::test_includes_header_info PASSED                                                      [ 29%]
tests/test_file_extractor.py::TestExtractTextFromCsv::test_truncates_large_csv PASSED                                                       [ 29%]
tests/test_file_extractor.py::TestExtractText::test_routes_to_txt PASSED                                                                    [ 30%] 
tests/test_file_extractor.py::TestExtractText::test_routes_to_csv PASSED                                                                    [ 31%] 
tests/test_file_extractor.py::TestExtractText::test_raises_for_unsupported_type PASSED                                                      [ 32%] 
tests/test_file_extractor.py::TestExtractFromUpload::test_extracts_from_bytes PASSED                                                        [ 32%] 
tests/test_file_extractor.py::TestExtractFromUpload::test_returns_text_length PASSED                                                        [ 33%]
tests/test_file_extractor.py::TestExtractFromUpload::test_truncates_long_text PASSED                                                        [ 34%] 
tests/test_file_extractor.py::TestExtractFromUpload::test_cleans_up_temp_file PASSED                                                        [ 35%] 
tests/test_file_extractor.py::TestExtractFromUpload::test_csv_extraction PASSED                                                             [ 35%] 
tests/test_files_route.py::TestGetFileExtension::test_extracts_pdf_extension PASSED                                                         [ 36%] 
tests/test_files_route.py::TestGetFileExtension::test_extracts_txt_extension PASSED                                                         [ 37%] 
tests/test_files_route.py::TestGetFileExtension::test_extracts_csv_extension PASSED                                                         [ 38%]
tests/test_files_route.py::TestGetFileExtension::test_extracts_docx_extension PASSED                                                        [ 38%] 
tests/test_files_route.py::TestGetFileExtension::test_extracts_xlsx_extension PASSED                                                        [ 39%]
tests/test_files_route.py::TestGetFileExtension::test_handles_multiple_dots PASSED                                                          [ 40%] 
tests/test_files_route.py::TestGetFileExtension::test_returns_lowercase PASSED                                                              [ 41%] 
tests/test_files_route.py::TestGetFileExtension::test_returns_empty_for_no_extension PASSED                                                 [ 41%] 
tests/test_files_route.py::TestGetFileExtension::test_handles_empty_string PASSED                                                           [ 42%] 
tests/test_files_route.py::TestGetFileExtension::test_handles_dot_only PASSED                                                               [ 43%] 
tests/test_files_route.py::TestAllowedExtensions::test_includes_pdf PASSED                                                                  [ 44%] 
tests/test_files_route.py::TestAllowedExtensions::test_includes_txt PASSED                                                                  [ 45%] 
tests/test_files_route.py::TestAllowedExtensions::test_includes_csv PASSED                                                                  [ 45%] 
tests/test_files_route.py::TestAllowedExtensions::test_includes_docx PASSED                                                                 [ 46%] 
tests/test_files_route.py::TestAllowedExtensions::test_includes_xlsx PASSED                                                                 [ 47%] 
tests/test_files_route.py::TestAllowedExtensions::test_does_not_include_exe PASSED                                                          [ 48%] 
tests/test_files_route.py::TestAllowedExtensions::test_does_not_include_js PASSED                                                           [ 48%] 
tests/test_files_route.py::TestAllowedExtensions::test_is_set PASSED                                                                        [ 49%] 
tests/test_files_route.py::TestExtractFileContentEndpoint::test_rejects_unsupported_file_type PASSED                                        [ 50%]
tests/test_files_route.py::TestExtractFileContentEndpoint::test_extracts_txt_file PASSED                                                    [ 51%]
tests/test_files_route.py::TestExtractFileContentEndpoint::test_returns_extraction_metadata PASSED                                          [ 51%]
tests/test_files_route.py::TestFileLimitsEndpoint::test_returns_limits PASSED                                                               [ 52%]
tests/test_files_route.py::TestFileLimitsEndpoint::test_allowed_extensions_match PASSED                                                     [ 53%]
tests/test_kafka_producer.py::TestPublishChatRequest::test_publishes_message_with_request_id PASSED                                         [ 54%]
tests/test_kafka_producer.py::TestPublishChatRequest::test_includes_all_data_fields PASSED                                                  [ 54%] 
tests/test_kafka_producer.py::TestPublishFileRequest::test_publishes_to_file_topic PASSED                                                   [ 55%] 
tests/test_kafka_producer.py::TestPublishRagdataRequest::test_publishes_to_ragdata_topic PASSED                                             [ 56%]
tests/test_kafka_producer.py::TestPublishRagdataDelete::test_publishes_delete_action PASSED                                                 [ 57%] 
tests/test_kafka_producer.py::TestConnectKafka::test_retries_on_failure PASSED                                                              [ 58%] 
tests/test_kafka_producer.py::TestCloseKafka::test_stops_producer PASSED                                                                    [ 58%] 
tests/test_kafka_producer.py::TestCloseKafka::test_handles_none_producer PASSED                                                             [ 59%] 
tests/test_models.py::TestMessage::test_creates_valid_message PASSED                                                                        [ 60%] 
tests/test_models.py::TestMessage::test_accepts_user_role PASSED                                                                            [ 61%] 
tests/test_models.py::TestMessage::test_accepts_assistant_role PASSED                                                                       [ 61%] 
tests/test_models.py::TestMessage::test_requires_role PASSED                                                                                [ 62%] 
tests/test_models.py::TestMessage::test_requires_content PASSED                                                                             [ 63%] 
tests/test_models.py::TestMessage::test_accepts_custom_timestamp PASSED                                                                     [ 64%] 
tests/test_models.py::TestMessage::test_default_timestamp_is_now PASSED                                                                     [ 64%] 
tests/test_models.py::TestChatRequest::test_creates_with_message_only PASSED                                                                [ 65%] 
tests/test_models.py::TestChatRequest::test_accepts_all_fields PASSED                                                                       [ 66%] 
tests/test_models.py::TestChatRequest::test_requires_message PASSED                                                                         [ 67%] 
tests/test_models.py::TestChatRequest::test_allows_empty_message PASSED                                                                     [ 67%] 
tests/test_models.py::TestChatSendResponse::test_creates_valid_response PASSED                                                              [ 68%]
tests/test_models.py::TestChatSendResponse::test_requires_both_fields PASSED                                                                [ 69%] 
tests/test_models.py::TestStreamResponse::test_creates_processing_response PASSED                                                           [ 70%] 
tests/test_models.py::TestStreamResponse::test_creates_completed_response PASSED                                                            [ 70%] 
tests/test_models.py::TestStreamResponse::test_creates_error_response PASSED                                                                [ 71%] 
tests/test_models.py::TestStreamResponse::test_default_finished_is_zero PASSED                                                              [ 72%] 
tests/test_models.py::TestConversationListItem::test_creates_valid_item PASSED                                                              [ 73%] 
tests/test_models.py::TestConversationListItem::test_default_message_count PASSED                                                           [ 74%] 
tests/test_models.py::TestConversationDetail::test_creates_with_messages PASSED                                                             [ 74%] 
tests/test_models.py::TestConversationDetail::test_default_empty_file_ids PASSED                                                            [ 75%] 
tests/test_models.py::TestConversationDetail::test_accepts_file_ids PASSED                                                                  [ 76%] 
tests/test_redis_client.py::TestGetResult::test_returns_parsed_result PASSED                                                                [ 77%] 
tests/test_redis_client.py::TestGetResult::test_returns_none_when_not_found PASSED                                                          [ 77%]
tests/test_redis_client.py::TestGetResult::test_uses_correct_key_prefix PASSED                                                              [ 78%] 
tests/test_redis_client.py::TestDeleteResult::test_deletes_with_correct_key PASSED                                                          [ 79%] 
tests/test_redis_client.py::TestConnectRedis::test_connects_and_pings PASSED                                                                [ 80%]
tests/test_redis_client.py::TestCloseRedis::test_closes_connection PASSED                                                                   [ 80%] 
tests/test_redis_client.py::TestCloseRedis::test_handles_none_client PASSED                                                                 [ 81%] 
tests/test_security.py::TestCheckRateLimit::test_allows_first_request PASSED                                                                [ 82%] 
tests/test_security.py::TestCheckRateLimit::test_allows_requests_under_limit PASSED                                                         [ 83%] 
tests/test_security.py::TestCheckRateLimit::test_blocks_requests_over_limit PASSED                                                          [ 83%] 
tests/test_security.py::TestCheckRateLimit::test_different_keys_independent PASSED                                                          [ 84%] 
tests/test_security.py::TestValidateInput::test_valid_normal_text PASSED                                                                    [ 85%] 
tests/test_security.py::TestValidateInput::test_rejects_too_long_input PASSED                                                               [ 86%] 
tests/test_security.py::TestValidateInput::test_rejects_script_tags PASSED                                                                  [ 87%] 
tests/test_security.py::TestValidateInput::test_rejects_javascript_urls PASSED                                                              [ 87%] 
tests/test_security.py::TestValidateInput::test_rejects_event_handlers PASSED                                                               [ 88%] 
tests/test_security.py::TestValidateInput::test_empty_is_valid PASSED                                                                       [ 89%] 
tests/test_security.py::TestValidateFilename::test_valid_filename PASSED                                                                    [ 90%] 
tests/test_security.py::TestValidateFilename::test_rejects_empty_filename PASSED                                                            [ 90%]
tests/test_security.py::TestValidateFilename::test_rejects_path_traversal PASSED                                                            [ 91%] 
tests/test_security.py::TestValidateFilename::test_rejects_forward_slash PASSED                                                             [ 92%] 
tests/test_security.py::TestValidateFilename::test_rejects_backslash PASSED                                                                 [ 93%] 
tests/test_security.py::TestValidateFilename::test_rejects_null_bytes PASSED                                                                [ 93%] 
tests/test_security.py::TestValidateFilename::test_rejects_too_long_filename PASSED                                                         [ 94%]
tests/test_security.py::TestValidateJsonContent::test_valid_shallow_json PASSED                                                             [ 95%] 
tests/test_security.py::TestValidateJsonContent::test_valid_nested_json PASSED                                                              [ 96%]
tests/test_security.py::TestValidateJsonContent::test_rejects_deeply_nested_json PASSED                                                     [ 96%] 
tests/test_security.py::TestValidateJsonContent::test_handles_arrays PASSED                                                                 [ 97%] 
tests/test_security.py::TestGetClientIp::test_extracts_from_forwarded_header PASSED                                                         [ 98%] 
tests/test_security.py::TestGetClientIp::test_falls_back_to_client_host PASSED                                                              [ 99%] 
tests/test_security.py::TestGetClientIp::test_handles_missing_client PASSED                                                                 [100%] 



# Orchestrator Unit Tests

Documentation of unit tests coverage for the Orchestrator service.

## Test Files Overview

| File | Tests | Description |
|------|-------|-------------|
| `test_chat_handler.py` | 20 | Chat message handling & token management |
| `test_config.py` | 17 | Configuration settings & retry logic |
| `test_dlq_handler.py` | 15 | Dead Letter Queue operations |
| `test_main_dlq.py` | 12 | DLQ API endpoints |
| `test_redis_client.py` | 9 | Redis caching operations |
| `test_retry_handler.py` | 17 | Retry logic & backoff calculations |
| `test_retry_producer.py` | 6 | Kafka retry producer |
| `test_security.py` | 30+ | Security utilities & input validation |

---

## 1. Chat Handler (`test_chat_handler.py`)

### Token Estimation
- `test_estimates_short_text` - Estimates tokens for short text
- `test_estimates_longer_text` - Estimates tokens for longer text
- `test_empty_string_returns_zero` - Empty string returns 0 tokens
- `test_none_returns_zero` - None returns 0 tokens
- `test_whitespace_counted` - Whitespace is counted in token estimation

### Token Truncation
- `test_short_text_unchanged` - Short text is not truncated
- `test_long_text_truncated` - Long text is truncated to limit
- `test_truncation_adds_message` - Truncated text includes truncation notice
- `test_exact_length_not_truncated` - Text at exact limit is not truncated

### Message Content Truncation
- `test_regular_message_unchanged` - Regular messages are preserved
- `test_long_message_truncated` - Long messages are truncated
- `test_file_content_handled_separately` - File content handled separately from user text
- `test_preserves_file_marker` - File attachment markers are preserved
- `test_very_long_user_text_omits_file` - Very long user text may omit file content

### Message Building with Token Limit
- `test_includes_current_message` - Current message is always included
- `test_empty_messages_returns_empty` - Empty message list returns empty
- `test_single_message` - Single message is handled correctly
- `test_limits_history` - History is limited to fit token budget
- `test_prioritizes_recent_history` - Recent messages are prioritized over old

### Integration
- `test_handles_basic_message` - End-to-end test for basic chat message processing

---

## 2. Configuration (`test_config.py`)

### Retryable Error Detection
- `test_timeout_error_is_retryable` - Timeout errors trigger retry
- `test_rate_limit_error_is_retryable` - Rate limit errors trigger retry
- `test_connection_error_is_retryable` - Connection errors trigger retry
- `test_network_error_is_retryable` - Network errors trigger retry
- `test_503_error_is_retryable` - HTTP 503 errors trigger retry
- `test_504_error_is_retryable` - HTTP 504 errors trigger retry
- `test_429_error_is_retryable` - HTTP 429 errors trigger retry
- `test_temporary_error_is_retryable` - Temporary errors trigger retry
- `test_unavailable_error_is_retryable` - Service unavailable errors trigger retry
- `test_overloaded_error_is_retryable` - Server overloaded errors trigger retry
- `test_validation_error_not_retryable` - Validation errors do NOT trigger retry
- `test_auth_error_not_retryable` - Authentication errors do NOT trigger retry
- `test_not_found_error_not_retryable` - Not found errors do NOT trigger retry
- `test_permission_error_not_retryable` - Permission errors do NOT trigger retry
- `test_case_insensitive` - Error detection is case-insensitive
- `test_empty_error_message` - Empty error messages handled correctly

### Settings Defaults
- `test_default_max_retry_count` - Default MAX_RETRY_COUNT = 5
- `test_default_backoff_base` - Default RETRY_BACKOFF_BASE = 1.0
- `test_default_backoff_multiplier` - Default RETRY_BACKOFF_MULTIPLIER = 2.0
- `test_default_backoff_max` - Default RETRY_BACKOFF_MAX = 120.0
- `test_default_jitter_max` - Default RETRY_JITTER_MAX = 2.0
- `test_default_max_workers` - Default MAX_WORKERS = 10
- `test_default_redis_ttl` - Default REDIS_RESULT_TTL = 300

---

## 3. Dead Letter Queue Handler (`test_dlq_handler.py`)

### DLQ Item Model
- `test_creates_valid_item` - Create valid DLQ item with all fields
- `test_requires_all_fields` - Validation requires all fields

### Save to DLQ
- `test_creates_new_entry` - Creates new DLQ entry when not exists
- `test_updates_existing_entry` - Updates existing entry (idempotency)

### Get DLQ Items
- `test_returns_list_of_items` - Returns list of DLQ items
- `test_filters_by_status` - Filters items by status
- `test_respects_pagination` - Respects limit and skip parameters

### Get DLQ Item Detail
- `test_returns_full_item` - Returns full item with message_data
- `test_returns_none_when_not_found` - Returns None for non-existent item

### Mark DLQ Retried
- `test_updates_status_to_retried` - Updates status to 'retried'
- `test_increments_retry_count` - Increments retry_count field

### Mark DLQ Resolved
- `test_updates_status_to_resolved` - Updates status to 'resolved'

### Delete DLQ Item
- `test_deletes_item` - Successfully deletes item
- `test_returns_false_when_not_found` - Returns False when item not found

### DLQ Statistics
- `test_returns_status_counts` - Returns counts by status (pending, retried, resolved)
- `test_includes_topic_breakdown` - Includes breakdown by original topic

---

## 4. DLQ API Endpoints (`test_main_dlq.py`)

### GET /api/dlq/stats
- `test_returns_stats` - Returns DLQ statistics with retry config

### GET /api/dlq/items
- `test_returns_items_list` - Returns list of DLQ items
- `test_filters_by_status` - Filters by status query parameter
- `test_respects_pagination` - Respects limit and skip parameters

### GET /api/dlq/items/{id}
- `test_returns_item_detail` - Returns full item detail
- `test_returns_404_when_not_found` - Returns 404 for non-existent item

### POST /api/dlq/items/{id}/retry
- `test_retries_item` - Re-publishes item to original topic
- `test_returns_404_for_nonexistent` - Returns 404 for non-existent item

### POST /api/dlq/items/{id}/resolve
- `test_resolves_item` - Marks item as resolved

### DELETE /api/dlq/items/{id}
- `test_deletes_item` - Deletes DLQ item permanently
- `test_returns_404_when_not_found` - Returns 404 for non-existent item

### POST /api/dlq/retry-all
- `test_retries_all_pending` - Retries all pending items

---

## 5. Redis Client (`test_redis_client.py`)

### Stream Update
- `test_updates_redis_with_content` - Updates Redis with streaming content
- `test_sets_finished_flag` - Sets finished flag when complete

### Set Result
- `test_stores_result_with_ttl` - Stores result with TTL
- `test_serializes_result_to_json` - Serializes result to JSON

### Set Error
- `test_stores_error_with_status` - Stores error with status flag

### Get Result
- `test_returns_parsed_result` - Returns parsed result from Redis
- `test_returns_none_when_not_found` - Returns None when key not found

### Connection Management
- `test_connects_and_pings` - Connect and ping Redis
- `test_closes_connection` - Close Redis connection properly

---

## 6. Retry Handler (`test_retry_handler.py`)

### Backoff Delay Calculation
- `test_first_retry_delay` - First retry delay is 2s (base * 2^1)
- `test_second_retry_delay` - Second retry delay is 4s (base * 2^2)
- `test_third_retry_delay` - Third retry delay is 8s (base * 2^3)
- `test_respects_max_backoff` - Delay does not exceed max_backoff
- `test_adds_jitter` - Delay includes random jitter
- `test_zero_retry_count` - Zero retry uses base delay

### Should Retry Decision
- `test_retry_when_under_limit` - Retry when retry_count < max
- `test_no_retry_when_at_limit` - No retry when retry_count >= max
- `test_no_retry_when_over_limit` - No retry when over limit

### Retry Payload Creation
- `test_creates_payload_with_retry_info` - Creates payload with _retry field
- `test_increments_retry_count` - Increments retry_count
- `test_preserves_original_topic` - Preserves original topic
- `test_includes_error_history` - Includes error message in history
- `test_includes_timestamp` - Includes last_attempt timestamp
- `test_includes_next_delay` - Includes calculated next delay

### Extract Retry Info
- `test_extracts_retry_info` - Extracts _retry field from data
- `test_removes_retry_from_data` - Removes _retry from original data
- `test_returns_none_when_no_retry` - Returns None when no _retry field

### Wait for Backoff
- `test_waits_for_calculated_delay` - Waits for calculated backoff delay

---

## 7. Retry Producer (`test_retry_producer.py`)

### Publish to Retry Queue
- `test_publishes_to_retry_topic` - Publishes message to retry topic
- `test_initializes_producer_if_needed` - Initializes producer if not exists

### Republish to Original Topic
- `test_publishes_to_specified_topic` - Publishes to specified original topic

### Producer Lifecycle
- `test_creates_kafka_producer` - Creates and starts Kafka producer
- `test_stops_producer` - Stops producer properly
- `test_handles_none_producer` - Handles None producer gracefully

---

## 8. Security (`test_security.py`)

### Prompt Injection Detection
- `test_detects_ignore_instructions` - Detects "ignore previous instructions" pattern
- `test_detects_disregard_instructions` - Detects "disregard" pattern
- `test_detects_system_marker` - Detects "system:" marker injection
- `test_detects_role_manipulation` - Detects "you are now a" manipulation
- `test_detects_jailbreak_attempts` - Detects DAN mode/jailbreak keywords
- `test_detects_prompt_extraction` - Detects system prompt extraction attempts
- `test_detects_tool_hijacking` - Detects tool/function hijacking
- `test_normal_text_not_flagged` - Normal text is not flagged
- `test_case_insensitive` - Detection is case-insensitive
- `test_empty_text` - Empty text is not flagged

### Input Sanitization
- `test_removes_script_tags` - Removes script tags
- `test_removes_event_handlers` - Removes onclick/onerror handlers
- `test_removes_javascript_urls` - Removes javascript: URLs
- `test_preserves_normal_text` - Preserves normal text
- `test_handles_empty_input` - Handles empty input

### File Content Sanitization
- `test_handles_large_content` - Handles large file content
- `test_preserves_valid_content` - Preserves valid content
- `test_removes_dangerous_tags` - Removes dangerous tags from files

### PII Masking
- `test_masks_email` - Masks email addresses
- `test_masks_phone_number` - Masks phone numbers
- `test_masks_credit_card` - Masks credit card numbers
- `test_no_pii_detected` - Returns original text when no PII
- `test_multiple_pii_types` - Detects multiple PII types

### System Prompt Leak Detection
- `test_detects_exact_phrase_match` - Detects when response contains system prompt phrases
- `test_detects_leak_indicators` - Detects common leak indicator phrases
- `test_no_false_positive_normal_response` - Normal responses are not flagged
- `test_empty_inputs` - Handles empty inputs

### User Access Validation
- `test_same_user_allowed` - Same user has access
- `test_different_user_denied` - Different user is denied
- `test_empty_user_denied` - Empty user is denied
- `test_none_user_denied` - None user is denied

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_chat_handler.py

# Run specific test class
pytest tests/test_security.py::TestDetectPromptInjection

# Run with verbose output
pytest -v
```

## Test Configuration

See `pytest.ini` for test configuration:
- Test paths: `tests/`
- Async mode: `auto`
- Output: `-v --tb=short`


## Result ( run pytest inside orchestrator container)
root@40b83d52dd65:/app# pytest 
=============================================================== test session starts ===============================================================
platform linux -- Python 3.11.14, pytest-8.0.2, pluggy-1.6.0 -- /usr/local/bin/python3.11
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.12.1, asyncio-0.23.5, cov-4.1.0
asyncio: mode=Mode.AUTO
collected 146 items                                                                                                                               

tests/test_chat_handler.py::TestEstimateTokens::test_estimates_short_text PASSED                                                            [  0%]
tests/test_chat_handler.py::TestEstimateTokens::test_estimates_longer_text PASSED                                                           [  1%] 
tests/test_chat_handler.py::TestEstimateTokens::test_empty_string_returns_zero PASSED                                                       [  2%] 
tests/test_chat_handler.py::TestEstimateTokens::test_none_returns_zero PASSED                                                               [  2%] 
tests/test_chat_handler.py::TestEstimateTokens::test_whitespace_counted PASSED                                                              [  3%] 
tests/test_chat_handler.py::TestTruncateToTokens::test_short_text_unchanged PASSED                                                          [  4%] 
tests/test_chat_handler.py::TestTruncateToTokens::test_long_text_truncated PASSED                                                           [  4%] 
tests/test_chat_handler.py::TestTruncateToTokens::test_truncation_adds_message PASSED                                                       [  5%] 
tests/test_chat_handler.py::TestTruncateToTokens::test_exact_length_not_truncated PASSED                                                    [  6%] 
tests/test_chat_handler.py::TestTruncateMessageContent::test_regular_message_unchanged PASSED                                               [  6%] 
tests/test_chat_handler.py::TestTruncateMessageContent::test_long_message_truncated PASSED                                                  [  7%]
tests/test_chat_handler.py::TestTruncateMessageContent::test_file_content_handled_separately PASSED                                         [  8%] 
tests/test_chat_handler.py::TestTruncateMessageContent::test_preserves_file_marker PASSED                                                   [  8%] 
tests/test_chat_handler.py::TestTruncateMessageContent::test_very_long_user_text_omits_file PASSED                                          [  9%] 
tests/test_chat_handler.py::TestBuildMessagesWithTokenLimit::test_includes_current_message PASSED                                           [ 10%] 
tests/test_chat_handler.py::TestBuildMessagesWithTokenLimit::test_empty_messages_returns_empty PASSED                                       [ 10%] 
tests/test_chat_handler.py::TestBuildMessagesWithTokenLimit::test_single_message PASSED                                                     [ 11%] 
tests/test_chat_handler.py::TestBuildMessagesWithTokenLimit::test_limits_history PASSED                                                     [ 12%]
tests/test_chat_handler.py::TestBuildMessagesWithTokenLimit::test_prioritizes_recent_history PASSED                                         [ 13%] 
tests/test_chat_handler.py::TestHandleChatRequest::test_handles_basic_message PASSED                                                        [ 13%]
tests/test_config.py::TestIsRetryableError::test_timeout_error_is_retryable PASSED                                                          [ 14%] 
tests/test_config.py::TestIsRetryableError::test_rate_limit_error_is_retryable PASSED                                                       [ 15%] 
tests/test_config.py::TestIsRetryableError::test_connection_error_is_retryable PASSED                                                       [ 15%] 
tests/test_config.py::TestIsRetryableError::test_network_error_is_retryable PASSED                                                          [ 16%] 
tests/test_config.py::TestIsRetryableError::test_503_error_is_retryable PASSED                                                              [ 17%] 
tests/test_config.py::TestIsRetryableError::test_504_error_is_retryable PASSED                                                              [ 17%] 
tests/test_config.py::TestIsRetryableError::test_429_error_is_retryable PASSED                                                              [ 18%] 
tests/test_config.py::TestIsRetryableError::test_temporary_error_is_retryable PASSED                                                        [ 19%] 
tests/test_config.py::TestIsRetryableError::test_unavailable_error_is_retryable PASSED                                                      [ 19%] 
tests/test_config.py::TestIsRetryableError::test_overloaded_error_is_retryable PASSED                                                       [ 20%] 
tests/test_config.py::TestIsRetryableError::test_validation_error_not_retryable PASSED                                                      [ 21%] 
tests/test_config.py::TestIsRetryableError::test_auth_error_not_retryable PASSED                                                            [ 21%] 
tests/test_config.py::TestIsRetryableError::test_not_found_error_not_retryable PASSED                                                       [ 22%] 
tests/test_config.py::TestIsRetryableError::test_permission_error_not_retryable PASSED                                                      [ 23%] 
tests/test_config.py::TestIsRetryableError::test_case_insensitive PASSED                                                                    [ 23%] 
tests/test_config.py::TestIsRetryableError::test_empty_error_message PASSED                                                                 [ 24%] 
tests/test_config.py::TestRetryableErrors::test_contains_timeout PASSED                                                                     [ 25%] 
tests/test_config.py::TestRetryableErrors::test_contains_rate_limit PASSED                                                                  [ 26%] 
tests/test_config.py::TestRetryableErrors::test_contains_connection PASSED                                                                  [ 26%] 
tests/test_config.py::TestRetryableErrors::test_contains_http_error_codes PASSED                                                            [ 27%] 
tests/test_config.py::TestSettings::test_default_max_retry_count PASSED                                                                     [ 28%]
tests/test_config.py::TestSettings::test_default_backoff_base PASSED                                                                        [ 28%]
tests/test_config.py::TestSettings::test_default_backoff_multiplier PASSED                                                                  [ 29%]
tests/test_config.py::TestSettings::test_default_backoff_max PASSED                                                                         [ 30%]
tests/test_config.py::TestSettings::test_default_jitter_max PASSED                                                                          [ 30%]
tests/test_config.py::TestSettings::test_default_max_workers PASSED                                                                         [ 31%]
tests/test_config.py::TestSettings::test_default_redis_ttl PASSED                                                                           [ 32%]
tests/test_dlq_handler.py::TestDLQItemModel::test_creates_valid_item PASSED                                                                 [ 32%] 
tests/test_dlq_handler.py::TestDLQItemModel::test_requires_all_fields PASSED                                                                [ 33%] 
tests/test_dlq_handler.py::TestSaveToDLQ::test_creates_new_entry PASSED                                                                     [ 34%]
tests/test_dlq_handler.py::TestSaveToDLQ::test_updates_existing_entry PASSED                                                                [ 34%] 
tests/test_dlq_handler.py::TestGetDLQItems::test_returns_items_list PASSED                                                                  [ 35%] 
tests/test_dlq_handler.py::TestGetDLQItems::test_filters_by_status PASSED                                                                   [ 36%] 
tests/test_dlq_handler.py::TestGetDLQItems::test_respects_limit_and_skip PASSED                                                             [ 36%]
tests/test_dlq_handler.py::TestGetDLQItemDetail::test_returns_item_detail PASSED                                                            [ 37%]
tests/test_dlq_handler.py::TestGetDLQItemDetail::test_returns_none_when_not_found PASSED                                                    [ 38%]
tests/test_dlq_handler.py::TestGetDLQItemDetail::test_handles_invalid_id PASSED                                                             [ 39%]
tests/test_dlq_handler.py::TestMarkDLQRetried::test_updates_status_to_retried PASSED                                                        [ 39%]
tests/test_dlq_handler.py::TestMarkDLQResolved::test_updates_status_to_resolved PASSED                                                      [ 40%]
tests/test_dlq_handler.py::TestDeleteDLQItem::test_deletes_item PASSED                                                                      [ 41%]
tests/test_dlq_handler.py::TestDeleteDLQItem::test_returns_false_when_not_found PASSED                                                      [ 41%]
tests/test_dlq_handler.py::TestGetDLQStats::test_returns_status_counts PASSED                                                               [ 42%]
tests/test_dlq_handler.py::TestGetDLQStats::test_includes_topic_breakdown PASSED                                                            [ 43%]
tests/test_main_dlq.py::TestDLQStatsEndpoint::test_returns_stats PASSED                                                                     [ 43%]
tests/test_main_dlq.py::TestDLQListEndpoint::test_returns_items_list PASSED                                                                 [ 44%]
tests/test_main_dlq.py::TestDLQListEndpoint::test_filters_by_status PASSED                                                                  [ 45%]
tests/test_main_dlq.py::TestDLQListEndpoint::test_respects_pagination PASSED                                                                [ 45%]
tests/test_main_dlq.py::TestDLQItemDetailEndpoint::test_returns_item_detail PASSED                                                          [ 46%] 
tests/test_main_dlq.py::TestDLQItemDetailEndpoint::test_returns_404_when_not_found PASSED                                                   [ 47%]
tests/test_main_dlq.py::TestDLQRetryEndpoint::test_retries_item PASSED                                                                      [ 47%]
tests/test_main_dlq.py::TestDLQRetryEndpoint::test_returns_404_when_not_found PASSED                                                        [ 48%] 
tests/test_main_dlq.py::TestDLQResolveEndpoint::test_resolves_item PASSED                                                                   [ 49%]
tests/test_main_dlq.py::TestDLQDeleteEndpoint::test_deletes_item PASSED                                                                     [ 50%]
tests/test_main_dlq.py::TestDLQDeleteEndpoint::test_returns_404_when_not_found PASSED                                                       [ 50%]
tests/test_main_dlq.py::TestDLQRetryAllEndpoint::test_retries_all_pending PASSED                                                            [ 51%]
tests/test_redis_client.py::TestStreamUpdate::test_updates_redis_with_content PASSED                                                        [ 52%]
tests/test_redis_client.py::TestStreamUpdate::test_sets_finished_flag PASSED                                                                [ 52%]
tests/test_redis_client.py::TestSetResult::test_stores_result_with_ttl PASSED                                                               [ 53%]
tests/test_redis_client.py::TestSetResult::test_serializes_result_to_json PASSED                                                            [ 54%]
tests/test_redis_client.py::TestSetError::test_stores_error_with_status PASSED                                                              [ 54%] 
tests/test_redis_client.py::TestGetResult::test_returns_parsed_result PASSED                                                                [ 55%]
tests/test_redis_client.py::TestGetResult::test_returns_none_when_not_found PASSED                                                          [ 56%]
tests/test_redis_client.py::TestConnectRedis::test_connects_and_pings PASSED                                                                [ 56%] 
tests/test_redis_client.py::TestCloseRedis::test_closes_connection PASSED                                                                   [ 57%] 
tests/test_retry_handler.py::TestCalculateBackoffDelay::test_first_retry_delay PASSED                                                       [ 58%]
tests/test_retry_handler.py::TestCalculateBackoffDelay::test_second_retry_delay PASSED                                                      [ 58%] 
tests/test_retry_handler.py::TestCalculateBackoffDelay::test_third_retry_delay PASSED                                                       [ 59%] 
tests/test_retry_handler.py::TestCalculateBackoffDelay::test_respects_max_backoff PASSED                                                    [ 60%] 
tests/test_retry_handler.py::TestCalculateBackoffDelay::test_adds_jitter PASSED                                                             [ 60%] 
tests/test_retry_handler.py::TestCalculateBackoffDelay::test_zero_retry_count PASSED                                                        [ 61%] 
tests/test_retry_handler.py::TestShouldRetry::test_retries_timeout_error PASSED                                                             [ 62%]
tests/test_retry_handler.py::TestShouldRetry::test_retries_rate_limit_error PASSED                                                          [ 63%] 
tests/test_retry_handler.py::TestShouldRetry::test_does_not_retry_validation_error PASSED                                                   [ 63%]
tests/test_retry_handler.py::TestShouldRetry::test_does_not_retry_when_max_reached PASSED                                                   [ 64%] 
tests/test_retry_handler.py::TestShouldRetry::test_does_not_retry_when_over_max PASSED                                                      [ 65%] 
tests/test_retry_handler.py::TestCreateRetryPayload::test_includes_original_data PASSED                                                     [ 65%] 
tests/test_retry_handler.py::TestCreateRetryPayload::test_includes_retry_metadata PASSED                                                    [ 66%]
tests/test_retry_handler.py::TestCreateRetryPayload::test_increments_retry_count PASSED                                                     [ 67%] 
tests/test_retry_handler.py::TestCreateRetryPayload::test_includes_timestamp PASSED                                                         [ 67%] 
tests/test_retry_handler.py::TestCreateRetryPayload::test_includes_next_delay PASSED                                                        [ 68%]
tests/test_retry_handler.py::TestExtractRetryInfo::test_extracts_retry_info PASSED                                                          [ 69%]
tests/test_retry_handler.py::TestExtractRetryInfo::test_removes_retry_from_data PASSED                                                      [ 69%] 
tests/test_retry_handler.py::TestExtractRetryInfo::test_returns_none_when_no_retry PASSED                                                   [ 70%] 
tests/test_retry_handler.py::TestWaitForBackoff::test_waits_for_calculated_delay PASSED                                                     [ 71%] 
tests/test_retry_producer.py::TestPublishToRetryQueue::test_publishes_to_retry_topic PASSED                                                 [ 71%] 
tests/test_retry_producer.py::TestPublishToRetryQueue::test_initializes_producer_if_needed PASSED                                           [ 72%] 
tests/test_retry_producer.py::TestRepublishToOriginalTopic::test_publishes_to_specified_topic PASSED                                        [ 73%] 
tests/test_retry_producer.py::TestInitRetryProducer::test_creates_kafka_producer PASSED                                                     [ 73%] 
tests/test_retry_producer.py::TestStopRetryProducer::test_stops_producer PASSED                                                             [ 74%] 
tests/test_retry_producer.py::TestStopRetryProducer::test_handles_none_producer PASSED                                                      [ 75%] 
tests/test_security.py::TestDetectPromptInjection::test_detects_ignore_instructions PASSED                                                  [ 76%] 
tests/test_security.py::TestDetectPromptInjection::test_detects_disregard_instructions PASSED                                               [ 76%] 
tests/test_security.py::TestDetectPromptInjection::test_detects_system_marker PASSED                                                        [ 77%] 
tests/test_security.py::TestDetectPromptInjection::test_detects_role_manipulation PASSED                                                    [ 78%] 
tests/test_security.py::TestDetectPromptInjection::test_detects_jailbreak_attempts PASSED                                                   [ 78%] 
tests/test_security.py::TestDetectPromptInjection::test_detects_prompt_extraction PASSED                                                    [ 79%] 
tests/test_security.py::TestDetectPromptInjection::test_detects_tool_hijacking PASSED                                                       [ 80%] 
tests/test_security.py::TestDetectPromptInjection::test_normal_text_not_flagged PASSED                                                      [ 80%] 
tests/test_security.py::TestDetectPromptInjection::test_case_insensitive PASSED                                                             [ 81%] 
tests/test_security.py::TestDetectPromptInjection::test_empty_text PASSED                                                                   [ 82%] 
tests/test_security.py::TestSanitizeInput::test_removes_script_tags PASSED                                                                  [ 82%]
tests/test_security.py::TestSanitizeInput::test_removes_javascript_urls PASSED                                                              [ 83%] 
tests/test_security.py::TestSanitizeInput::test_escapes_system_markers PASSED                                                               [ 84%] 
tests/test_security.py::TestSanitizeInput::test_preserves_normal_content PASSED                                                             [ 84%] 
tests/test_security.py::TestSanitizeInput::test_handles_empty_string PASSED                                                                 [ 85%] 
tests/test_security.py::TestSanitizeInput::test_handles_none PASSED                                                                         [ 86%] 
tests/test_security.py::TestSanitizeFileContent::test_adds_boundary_markers PASSED                                                          [ 86%] 
tests/test_security.py::TestSanitizeFileContent::test_warns_about_suspicious_content PASSED                                                 [ 87%] 
tests/test_security.py::TestSanitizeFileContent::test_sanitizes_content PASSED                                                              [ 88%] 
tests/test_security.py::TestMaskPII::test_masks_email PASSED                                                                                [ 89%] 
tests/test_security.py::TestMaskPII::test_masks_us_phone PASSED                                                                             [ 89%] 
tests/test_security.py::TestMaskPII::test_masks_credit_card PASSED                                                                          [ 90%]
tests/test_security.py::TestMaskPII::test_masks_ssn PASSED                                                                                  [ 91%] 
tests/test_security.py::TestMaskPII::test_partial_masking PASSED                                                                            [ 91%] 
tests/test_security.py::TestMaskPII::test_no_pii_detected PASSED                                                                            [ 92%] 
tests/test_security.py::TestMaskPII::test_multiple_pii_types PASSED                                                                         [ 93%] 
tests/test_security.py::TestCheckSystemPromptLeak::test_detects_exact_phrase_match PASSED                                                   [ 93%] 
tests/test_security.py::TestCheckSystemPromptLeak::test_detects_leak_indicators PASSED                                                      [ 94%] 
tests/test_security.py::TestCheckSystemPromptLeak::test_no_false_positive_normal_response PASSED                                            [ 95%] 
tests/test_security.py::TestCheckSystemPromptLeak::test_empty_inputs PASSED                                                                 [ 95%] 
tests/test_security.py::TestValidateUserAccess::test_same_user_allowed PASSED                                                               [ 96%] 
tests/test_security.py::TestValidateUserAccess::test_different_user_denied PASSED                                                           [ 97%] 
tests/test_security.py::TestValidateUserAccess::test_empty_user_denied PASSED                                                               [ 97%] 
tests/test_security.py::TestValidateUserAccess::test_none_user_denied PASSED                                                                [ 98%] 
tests/test_security.py::TestSecurityPatterns::test_injection_patterns_exist PASSED                                                          [ 99%] 
tests/test_security.py::TestSecurityPatterns::test_pii_patterns_exist PASSED                                                                [100%] 


# Frontend Unit Tests 

## 1. API Handlers (handlers.ts)

| API | Feature |
|-----|---------|
| `POST /api/auth/google` | Google login |
| `GET /api/auth/me` | Get current user information |
| `POST /api/auth/logout` | Logout |
| `GET /api/chat/conversations` | List conversations |
| `GET /api/chat/conversations/:id` | Conversation details |
| `POST /api/chat/send` | Send message |
| `DELETE /api/chat/conversations/:id` | Delete conversation |
| `GET /api/stream` | Poll LLM response |
| `POST /api/files/extract` | Upload and extract file content |

## 2. Error Cases (errorHandlers)

| Error | Description |
|-------|------------|
| `authError` | 401 Unauthorized |
| `networkError` | Network failure |
| `serverError` | 500 Internal Server Error |
| `rateLimitError` | 429 Rate Limit |

## 3. Mock Data Factories (factories.ts)

| Factory | Creates mock for |
|----------|-----------------|
| `createMockUser` | User object |
| `createMockMessage` | Message (user/assistant) |
| `createMockConversation` | Conversation list item |
| `createMockConversationDetail` | Conversation with messages |

## 4. Browser APIs Mock (setup.ts)

| API | Reason for Mocking |
|-----|-------------------|
| `matchMedia` | Responsive design |
| `IntersectionObserver` | Lazy loading |
| `scrollIntoView` | Auto-scroll chat |

## Result (run vite test inside frontend container)
/app # npm run test 

> alice-chatbot-frontend@1.0.0 test
> vitest


 DEV  v1.6.1 /app

stderr | src/context/AuthContext.test.tsx > AuthContext > Login > should login successfully
Warning: An update to AuthProvider inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act        
    at AuthProvider (/app/src/context/AuthContext.tsx:17:25)

stderr | src/context/AuthContext.test.tsx > AuthContext > Logout > should logout successfully
Warning: An update to AuthProvider inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act        
    at AuthProvider (/app/src/context/AuthContext.tsx:17:25)

 ✓ src/test/factories.test.ts (6)
 ✓ src/utils/chat.test.ts (32)
 ✓ src/api/chat.test.ts (14) 1723ms
 ✓ src/components/FileUploadButton.test.tsx (10) 1665ms
 ✓ src/context/AuthContext.test.tsx (7) 2003ms
 ✓ src/api/files.test.ts (2)
 ✓ src/api/auth.test.ts (3)
 ✓ src/components/MessageBubble.test.tsx (14) 474ms

 Test Files  8 passed (8)
      Tests  88 passed (88)
   Start at  06:32:48
   Duration  20.78s (transform 10.22s, setup 16.68s, collect 25.56s, tests 6.35s, environment 38.87s, prepare 12.19s)
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

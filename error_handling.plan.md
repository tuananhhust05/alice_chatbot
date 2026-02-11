# Alice Chatbot - Error Handling & Retry Strategy

## Executive Summary

This document defines the error handling and retry strategy for Alice Chatbot, focusing on resilient task processing with queue-based retry mechanisms, exponential backoff, and Dead Letter Queue (DLQ) management.

---

## 1. Retry Fundamentals

### 1.1 What is Retry?

Retry is the mechanism to re-attempt failed tasks. However, improper retry implementation can cause:

| Risk | Description |
|------|-------------|
| Request Storm | Uncontrolled retries flood the system |
| Data Duplication | Same operation executed multiple times |
| System Self-Destruction | Cascading failures from retry loops |

**Golden Rule**: Retry must always be paired with queue management and policy enforcement.

### 1.2 When to Retry

#### Retriable Errors (Transient)

| Error Type | HTTP Status | Should Retry |
|------------|-------------|--------------|
| Timeout | 408, 504 | Yes |
| Network Error | N/A | Yes |
| Server Error | 5xx | Yes |
| Rate Limit | 429 | Yes (with backoff) |
| Service Unavailable | 503 | Yes |

#### Non-Retriable Errors (Permanent)

| Error Type | HTTP Status | Should Retry |
|------------|-------------|--------------|
| Validation Error | 400 | No |
| Authentication Failed | 401 | No |
| Permission Denied | 403 | No |
| Resource Not Found | 404 | No |
| Logic/Business Error | 422 | No |

**Decision Rule**: Only retry errors that have a chance of self-resolving.

---

## 2. System Architecture

### 2.1 Queue-Based Retry Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Producer   │────▶│    Kafka     │────▶│ Orchestrator │
│   (Backend)  │     │  (Primary)   │     │   (Worker)   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                          ┌───────┴───────┐
                                          │               │
                                     Success          Failure
                                          │               │
                                          ▼               ▼
                                    ┌──────────┐   ┌─────────────┐
                                    │ Complete │   │ Check Retry │
                                    └──────────┘   │   Count     │
                                                   └──────┬──────┘
                                                          │
                                          ┌───────────────┴───────────────┐
                                          │                               │
                                   retry_count < max              retry_count >= max
                                          │                               │
                                          ▼                               ▼
                                   ┌─────────────┐               ┌──────────────┐
                                   │ Kafka Retry │               │ Dead Letter  │
                                   │   Queue     │               │ Queue (DLQ)  │
                                   └──────┬──────┘               │  (MongoDB)   │
                                          │                      └──────────────┘
                                          │ (after backoff delay)
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │ Orchestrator │
                                   │   (Retry)    │
                                   └──────────────┘
```

### 2.2 Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Primary Queue | Kafka | Main task queue |
| Retry Queue | Kafka (kafka_retry) | Failed tasks awaiting retry |
| Dead Letter Queue | MongoDB | Permanently failed tasks |
| Worker | Orchestrator | Task processor |

---

## 3. Retry Policy

### 3.1 Task Message Schema

```json
{
  "job_id": "uuid-v4",
  "task_type": "chat_completion",
  "payload": {
    "session_id": "sess_123",
    "message": "Hello"
  },
  "metadata": {
    "created_at": "2026-02-11T10:00:00Z",
    "retry_count": 0,
    "max_retry": 5,
    "last_error": null,
    "last_retry_at": null,
    "idempotency_key": "idem_abc123"
  }
}
```

### 3.2 Retry Configuration

```python
# config/retry.py

RETRY_CONFIG = {
    "max_retry": 5,
    "base_delay_seconds": 1,
    "max_delay_seconds": 300,  # 5 minutes cap
    "exponential_base": 2,
    "jitter_max_seconds": 1,
    
    # Error classification
    "retriable_errors": [
        "TimeoutError",
        "ConnectionError",
        "ServiceUnavailable",
        "RateLimitExceeded",
        "KafkaError",
        "MongoNetworkError",
        "WeaviateTimeoutError",
    ],
    
    "non_retriable_errors": [
        "ValidationError",
        "AuthenticationError",
        "PermissionError",
        "NotFoundError",
        "BusinessLogicError",
    ]
}
```

### 3.3 Exponential Backoff with Jitter

```
Delay = min(base * 2^retry_count + random(0, jitter_max), max_delay)
```

| Retry # | Base Delay | Exponential | Jitter (0-1s) | Total Delay |
|---------|------------|-------------|---------------|-------------|
| 1 | 1s | 2s | +0.5s | ~2.5s |
| 2 | 1s | 4s | +0.8s | ~4.8s |
| 3 | 1s | 8s | +0.3s | ~8.3s |
| 4 | 1s | 16s | +0.9s | ~16.9s |
| 5 | 1s | 32s | +0.6s | ~32.6s |

**Why Jitter?**: Prevents thundering herd when 1000+ jobs retry simultaneously.

---

## 4. Implementation

### 4.1 Error Handler Service

```python
# services/error_handler.py

import random
import time
from datetime import datetime
from typing import Optional
from enum import Enum

class ErrorType(Enum):
    RETRIABLE = "retriable"
    NON_RETRIABLE = "non_retriable"

class ErrorHandler:
    def __init__(self, kafka_producer, mongodb_client, config):
        self.kafka = kafka_producer
        self.db = mongodb_client
        self.config = config
        self.dlq_collection = self.db["dead_letter_queue"]
    
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error as retriable or non-retriable."""
        error_name = type(error).__name__
        
        if error_name in self.config["retriable_errors"]:
            return ErrorType.RETRIABLE
        
        # Check for HTTP status codes
        if hasattr(error, "status_code"):
            if error.status_code in [408, 429, 500, 502, 503, 504]:
                return ErrorType.RETRIABLE
        
        return ErrorType.NON_RETRIABLE
    
    def calculate_delay(self, retry_count: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        base = self.config["base_delay_seconds"]
        exp_base = self.config["exponential_base"]
        max_delay = self.config["max_delay_seconds"]
        jitter_max = self.config["jitter_max_seconds"]
        
        exponential_delay = base * (exp_base ** retry_count)
        jitter = random.uniform(0, jitter_max)
        
        return min(exponential_delay + jitter, max_delay)
    
    async def handle_failure(
        self,
        job: dict,
        error: Exception,
        context: Optional[dict] = None
    ) -> dict:
        """Handle task failure with retry or DLQ routing."""
        
        error_type = self.classify_error(error)
        retry_count = job["metadata"]["retry_count"]
        max_retry = job["metadata"]["max_retry"]
        
        # Update job metadata
        job["metadata"]["last_error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context
        }
        
        # Non-retriable error → DLQ immediately
        if error_type == ErrorType.NON_RETRIABLE:
            await self._send_to_dlq(job, reason="non_retriable_error")
            return {"action": "dlq", "reason": "non_retriable"}
        
        # Max retries exceeded → DLQ
        if retry_count >= max_retry:
            await self._send_to_dlq(job, reason="max_retries_exceeded")
            return {"action": "dlq", "reason": "max_retries"}
        
        # Retry with backoff
        job["metadata"]["retry_count"] += 1
        job["metadata"]["last_retry_at"] = datetime.utcnow().isoformat()
        
        delay = self.calculate_delay(retry_count)
        await self._send_to_retry_queue(job, delay)
        
        return {
            "action": "retry",
            "retry_count": job["metadata"]["retry_count"],
            "delay_seconds": delay
        }
    
    async def _send_to_retry_queue(self, job: dict, delay: float):
        """Send job to Kafka retry queue with delay metadata."""
        job["metadata"]["scheduled_retry_at"] = (
            datetime.utcnow().timestamp() + delay
        )
        
        await self.kafka.send(
            topic="alice_retry_queue",
            value=job,
            headers=[("delay_seconds", str(delay).encode())]
        )
    
    async def _send_to_dlq(self, job: dict, reason: str):
        """Send job to MongoDB Dead Letter Queue."""
        dlq_entry = {
            "job_id": job["job_id"],
            "task_type": job["task_type"],
            "payload": job["payload"],
            "metadata": job["metadata"],
            "dlq_reason": reason,
            "dlq_timestamp": datetime.utcnow(),
            "status": "pending",  # pending, retried, resolved, ignored
            "resolution": None,
            "resolved_at": None,
            "resolved_by": None
        }
        
        await self.dlq_collection.insert_one(dlq_entry)
```

### 4.2 Retry Queue Consumer

```python
# services/retry_consumer.py

import asyncio
from datetime import datetime

class RetryQueueConsumer:
    def __init__(self, kafka_consumer, orchestrator, error_handler):
        self.kafka = kafka_consumer
        self.orchestrator = orchestrator
        self.error_handler = error_handler
    
    async def consume(self):
        """Consume from retry queue and process with delay."""
        async for message in self.kafka.subscribe("alice_retry_queue"):
            job = message.value
            
            # Check if delay has passed
            scheduled_at = job["metadata"].get("scheduled_retry_at", 0)
            now = datetime.utcnow().timestamp()
            
            if now < scheduled_at:
                # Re-queue with remaining delay
                remaining = scheduled_at - now
                await asyncio.sleep(min(remaining, 1))
                continue
            
            # Process the job
            try:
                await self.orchestrator.process(job)
            except Exception as e:
                await self.error_handler.handle_failure(job, e)
```

### 4.3 Idempotency Guard

```python
# services/idempotency.py

class IdempotencyGuard:
    def __init__(self, redis_client, mongodb_client):
        self.redis = redis_client
        self.db = mongodb_client
        self.processed_collection = self.db["processed_jobs"]
    
    async def is_processed(self, idempotency_key: str) -> bool:
        """Check if job was already processed."""
        # Fast check in Redis
        if await self.redis.exists(f"processed:{idempotency_key}"):
            return True
        
        # Fallback to MongoDB
        result = await self.processed_collection.find_one(
            {"idempotency_key": idempotency_key}
        )
        return result is not None
    
    async def mark_processed(
        self,
        idempotency_key: str,
        job_id: str,
        result: dict
    ):
        """Mark job as processed."""
        # Set in Redis (with 24h TTL)
        await self.redis.setex(
            f"processed:{idempotency_key}",
            86400,
            job_id
        )
        
        # Persist in MongoDB
        await self.processed_collection.insert_one({
            "idempotency_key": idempotency_key,
            "job_id": job_id,
            "processed_at": datetime.utcnow(),
            "result_summary": result.get("summary")
        })
    
    async def process_with_guard(self, job: dict, processor):
        """Process job with idempotency protection."""
        key = job["metadata"]["idempotency_key"]
        
        if await self.is_processed(key):
            return {"status": "skipped", "reason": "already_processed"}
        
        result = await processor(job)
        await self.mark_processed(key, job["job_id"], result)
        
        return result
```

---

## 5. Dead Letter Queue Management

### 5.1 DLQ Schema

```javascript
// MongoDB Collection: dead_letter_queue
{
  "_id": ObjectId,
  "job_id": "uuid",
  "task_type": "chat_completion",
  "payload": { /* original payload */ },
  "metadata": {
    "created_at": ISODate,
    "retry_count": 5,
    "max_retry": 5,
    "last_error": {
      "type": "TimeoutError",
      "message": "Connection timed out",
      "timestamp": ISODate,
      "context": { /* stack trace, etc */ }
    }
  },
  "dlq_reason": "max_retries_exceeded",
  "dlq_timestamp": ISODate,
  "status": "pending",  // pending, retried, resolved, ignored
  "resolution": {
    "action": "manual_retry",
    "notes": "Fixed external service"
  },
  "resolved_at": ISODate,
  "resolved_by": "admin@example.com"
}

// Indexes
db.dead_letter_queue.createIndex({ "status": 1, "dlq_timestamp": -1 })
db.dead_letter_queue.createIndex({ "task_type": 1, "status": 1 })
db.dead_letter_queue.createIndex({ "job_id": 1 }, { unique: true })
```

### 5.2 DLQ Operations

| Operation | Description |
|-----------|-------------|
| View | List all DLQ entries with filters |
| Retry | Re-queue job for processing |
| Resolve | Mark as manually resolved |
| Ignore | Mark as ignored (won't process) |
| Bulk Retry | Retry multiple jobs at once |
| Export | Export to CSV/JSON for analysis |
| Purge | Delete old resolved/ignored entries |

### 5.3 DLQ API Endpoints

```python
# routes/dlq.py

@router.get("/api/admin/dlq")
async def list_dlq_entries(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 20
):
    """List DLQ entries with filters."""
    pass

@router.get("/api/admin/dlq/{job_id}")
async def get_dlq_entry(job_id: str):
    """Get single DLQ entry details."""
    pass

@router.post("/api/admin/dlq/{job_id}/retry")
async def retry_dlq_entry(job_id: str):
    """Retry a failed job from DLQ."""
    pass

@router.post("/api/admin/dlq/{job_id}/resolve")
async def resolve_dlq_entry(
    job_id: str,
    resolution: ResolutionRequest
):
    """Mark DLQ entry as resolved."""
    pass

@router.post("/api/admin/dlq/{job_id}/ignore")
async def ignore_dlq_entry(job_id: str, reason: str):
    """Mark DLQ entry as ignored."""
    pass

@router.post("/api/admin/dlq/bulk-retry")
async def bulk_retry(job_ids: List[str]):
    """Retry multiple jobs from DLQ."""
    pass

@router.delete("/api/admin/dlq/purge")
async def purge_old_entries(
    before_date: datetime,
    status: List[str] = ["resolved", "ignored"]
):
    """Purge old resolved/ignored entries."""
    pass

@router.get("/api/admin/dlq/stats")
async def get_dlq_stats():
    """Get DLQ statistics."""
    pass
```

---

## 6. Monitoring & Alerting

### 6.1 Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `retry_queue_size` | Jobs in retry queue | > 1000 |
| `dlq_size` | Jobs in DLQ | > 100 |
| `retry_rate` | Retries per minute | > 500/min |
| `dlq_rate` | DLQ additions per minute | > 10/min |
| `avg_retry_count` | Average retries before success | > 3 |
| `error_rate_by_type` | Errors grouped by type | Monitor trends |

### 6.2 Alerting Rules

```yaml
# prometheus/alerts.yml

groups:
  - name: retry_alerts
    rules:
      - alert: HighRetryQueueSize
        expr: retry_queue_size > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Retry queue is growing"
          
      - alert: HighDLQRate
        expr: rate(dlq_entries_total[5m]) > 0.2
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "High rate of jobs going to DLQ"
          
      - alert: DLQSizeExceeded
        expr: dlq_size > 500
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "DLQ has too many unresolved entries"
```

---

## 7. Best Practices

### 7.1 Retry Checklist

- [ ] Every task has unique `job_id`
- [ ] Every task has `idempotency_key`
- [ ] Retry count is tracked and limited
- [ ] Exponential backoff is implemented
- [ ] Jitter is added to prevent thundering herd
- [ ] Errors are classified (retriable vs non-retriable)
- [ ] DLQ captures all permanently failed tasks
- [ ] DLQ has admin UI for manual intervention
- [ ] Metrics and alerts are configured

### 7.2 Idempotency Checklist

- [ ] All database writes use upsert or check-before-write
- [ ] All external API calls are idempotent or guarded
- [ ] Email/notification sends check for duplicates
- [ ] Vector embeddings use upsert with unique IDs
- [ ] Financial transactions have idempotency keys

### 7.3 Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Retry immediately on failure | Use exponential backoff |
| No retry limit | Set max_retry (recommend 3-5) |
| Retry non-retriable errors | Classify errors properly |
| No jitter | Add random delay component |
| No DLQ monitoring | Set up alerts and dashboards |
| Ignoring DLQ | Regular review and cleanup |

---

## 8. Implementation Roadmap

| Phase | Tasks | Timeline |
|-------|-------|----------|
| Phase 1 | Create Kafka retry topic, implement error handler | Day 1-2 |
| Phase 2 | Implement DLQ with MongoDB, add idempotency guard | Day 3-4 |
| Phase 3 | Build Admin DLQ management UI | Day 5-6 |
| Phase 4 | Add monitoring metrics and alerts | Day 7 |
| Phase 5 | Testing and documentation | Day 8 |

---

## 9. Configuration Reference

### 9.1 Environment Variables

```bash
# Retry Configuration
RETRY_MAX_ATTEMPTS=5
RETRY_BASE_DELAY_SECONDS=1
RETRY_MAX_DELAY_SECONDS=300
RETRY_EXPONENTIAL_BASE=2
RETRY_JITTER_MAX_SECONDS=1

# Kafka Topics
KAFKA_TOPIC_PRIMARY=alice_tasks
KAFKA_TOPIC_RETRY=alice_retry_queue

# DLQ Configuration
DLQ_COLLECTION=dead_letter_queue
DLQ_RETENTION_DAYS=30
```

### 9.2 Kafka Topic Configuration

```bash
# Create retry topic with appropriate retention
kafka-topics.sh --create \
  --topic alice_retry_queue \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000  # 7 days
```

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Author**: Alice Chatbot Team

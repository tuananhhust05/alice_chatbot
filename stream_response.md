# Streaming Response Architecture

## Overview

This document describes the streaming response mechanism for real-time chat responses using Kafka for request queuing and Redis Pub/Sub for response streaming.

## Architecture Diagram

```
┌──────────┐     ┌──────────┐     ┌───────┐     ┌─────────────┐     ┌───────┐
│  Client  │────▶│ Backend  │────▶│ Kafka │────▶│Orchestrator │────▶│ Redis │
│(Frontend)│     │          │     │       │     │             │     │Pub/Sub│
└──────────┘     └──────────┘     └───────┘     └─────────────┘     └───────┘
     ▲                │                                                  │
     │                │◀─────────────────────────────────────────────────┘
     │                │           (Subscribe to response channel)
     │◀───────────────┘
     │    (SSE Stream)
```

## Flow Description

### Step 1: Client Sends Request

```
POST /api/chat/send
{
    "conversation_id": "conv_123",
    "content": "Hello, how are you?"
}
```

**Frontend Actions:**
- Send chat message to Backend API
- Receive `request_id` in response
- Open SSE (Server-Sent Events) connection to stream endpoint

### Step 2: Backend Receives Request

```python
# Backend /api/chat/send endpoint
async def send_message(request: ChatRequest):
    # 1. Generate unique request_id
    request_id = str(uuid.uuid4())
    
    # 2. Save message to MongoDB
    message = await save_message(request)
    
    # 3. Push request to Kafka
    await kafka_producer.send(
        topic="chat_requests",
        value={
            "request_id": request_id,
            "conversation_id": request.conversation_id,
            "content": request.content,
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    # 4. Return request_id immediately (non-blocking)
    return {"request_id": request_id, "status": "processing"}
```

### Step 3: Client Opens Stream Channel

```
GET /api/chat/stream/{request_id}
Accept: text/event-stream
```

**Backend SSE Endpoint:**
```python
async def stream_response(request_id: str):
    # Subscribe to Redis channel for this request
    channel = f"response:{request_id}"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    
    async def event_generator():
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                
                if data["type"] == "chunk":
                    yield f"data: {json.dumps({'chunk': data['content']})}\n\n"
                
                elif data["type"] == "done":
                    yield f"data: {json.dumps({'done': True, 'message_id': data['message_id']})}\n\n"
                    break
                
                elif data["type"] == "error":
                    yield f"data: {json.dumps({'error': data['message']})}\n\n"
                    break
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### Step 4: Orchestrator Processes Request

```python
# Orchestrator Kafka Consumer
async def consume_chat_requests():
    async for message in kafka_consumer:
        request = message.value
        request_id = request["request_id"]
        channel = f"response:{request_id}"
        
        try:
            # Process with LLM (streaming)
            async for chunk in llm.stream_chat(request["content"]):
                # Publish each chunk to Redis
                await redis.publish(channel, json.dumps({
                    "type": "chunk",
                    "content": chunk
                }))
            
            # Save complete response to MongoDB
            message_id = await save_assistant_message(request, full_response)
            
            # Signal completion
            await redis.publish(channel, json.dumps({
                "type": "done",
                "message_id": str(message_id)
            }))
            
        except Exception as e:
            # Publish error
            await redis.publish(channel, json.dumps({
                "type": "error",
                "message": str(e)
            }))
```

### Step 5: Client Receives Stream

```javascript
// Frontend EventSource
const eventSource = new EventSource(`/api/chat/stream/${requestId}`);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.chunk) {
        // Append chunk to message display
        appendToMessage(data.chunk);
    }
    
    if (data.done) {
        // Streaming complete
        eventSource.close();
        finalizeMessage(data.message_id);
    }
    
    if (data.error) {
        // Handle error
        eventSource.close();
        showError(data.error);
    }
};
```

## Message Types in Redis Pub/Sub

| Type | Description | Payload |
|------|-------------|---------|
| `chunk` | Partial response text | `{"type": "chunk", "content": "Hello..."}` |
| `done` | Stream completed | `{"type": "done", "message_id": "msg_123"}` |
| `error` | Processing failed | `{"type": "error", "message": "LLM timeout"}` |
| `thinking` | Agent is processing | `{"type": "thinking", "step": "Searching..."}` |

## Redis Channel Naming Convention

```
response:{request_id}
```

Example: `response:550e8400-e29b-41d4-a716-446655440000`

## Timeout & Cleanup

| Component | Timeout | Action |
|-----------|---------|--------|
| SSE Connection | 5 minutes | Client reconnect with same request_id |
| Redis Channel | 10 minutes | Auto-expire (TTL) |
| Kafka Message | 24 hours | Retention policy |

## Error Handling

### Orchestrator Down
- Kafka retains messages until Orchestrator recovers
- Client shows "Processing..." with timeout warning

### Redis Connection Lost
- Backend falls back to polling MongoDB for response
- Graceful degradation to non-streaming mode

### Client Disconnects
- Orchestrator continues processing (fire-and-forget)
- Response saved to MongoDB for later retrieval

## Benefits

1. **Non-blocking**: Backend returns immediately, doesn't wait for LLM
2. **Scalable**: Kafka handles high throughput, multiple Orchestrator instances
3. **Real-time**: Sub-second latency for streaming chunks
4. **Resilient**: Messages persist in Kafka if Orchestrator is down
5. **Decoupled**: Backend and Orchestrator scale independently

## Implementation Checklist

- [ ] Backend: Kafka producer for chat requests
- [ ] Backend: SSE endpoint with Redis subscription
- [ ] Orchestrator: Kafka consumer for chat requests
- [ ] Orchestrator: Redis publisher for streaming chunks
- [ ] Frontend: EventSource client for SSE
- [ ] Redis: Channel TTL configuration
- [ ] Monitoring: Track stream latency and completion rate

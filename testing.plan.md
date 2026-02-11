0. Unit test for frontend, backend, ochestrator, dataflow 

1. Integration test (rất quan trọng)
- Unit test là chưa đủ vì chatbot hỏng thường do ghép hệ thống.
Nên test:
- FE ↔ Backend (API contract, schema, timeout)
- Backend ↔ LLM provider (OpenAI / Azure / internal LLM)
- Orchestrator ↔ tools (search, DB, RAG, workflow engine)
Dataflow end-to-end:
- user input → preprocess → intent → tool call → postprocess → response
👉 Tip: mock LLM ở mức semantic, không chỉ mock string.

2. Conversation / Dialogue test (stateful test)
- Chatbot ≠ API stateless.

Test các case:
- Multi-turn conversation (context có bị trôi không)
- Người dùng đổi ý giữa chừng
- Follow-up mơ hồ (“ý tôi là cái ở trên”)
- Conversation reset / expire session
- Parallel conversations (same user, multi tab)

👉 Có thể define conversation script:
User: A
Bot: ...
User: B (ref A)
Expected intent: X

3. Prompt & LLM behavior test
Đây là phần nhiều team bỏ sót.

Prompt regression test
- Khi sửa prompt → output có bị “lệch tính cách / policy” không
- Snapshot test cho prompt + expected traits (không snapshot full text)

Non-deterministic test
- Chạy 20–50 lần cùng input
- Assert theo rule:
  + Có/không có thông tin nhạy cảm
  + Có cấu trúc đúng (JSON, bullet, step)
  + Không hallucinate domain cấm

4. RAG & Data quality test
Nếu có retrieval thì test data quan trọng hơn test code.

Nên test:
- Recall test: câu hỏi X có retrieve đúng doc không
- Chunking test: chunk quá to / quá nhỏ
- Embedding drift khi update model
- Stale data / versioning

👉 Metrics hay dùng:
- Precision@k
- Answer grounded rate (answer có citation hay không)

5. Security & Safety test (enterprise bắt buộc)
Prompt injection
- “Ignore previous instructions…”
- User chèn instruction trong file upload
- Tool hijacking (“call this tool with …”)

Data leakage
- Chatbot có lộ PII không
- Có leak system prompt không
- Cross-tenant data access

6. Load & Cost test
Chatbot enterprise chết nhiều vì… tiền 💸

Test:
- Concurrent users (burst traffic)
- Token usage / conversation
- Long conversation (token overflow)
- Tool call storm (LLM gọi tool liên tục)

👉 Assert:
- max tokens
- max tool calls / turn
- graceful degradation (fallback answer)

7. UX & Human-in-the-loop test
Không chỉ đúng – mà phải dùng được.
- A/B test response style
- Human review sample conversation
- Test escalation (handoff sang human agent)
- Test feedback loop (thumb up/down → retrain)

8. Observability test (rất enterprise)
Test luôn cả khả năng debug khi prod lỗi:
- Log có trace được 1 conversation không
- Có correlation id xuyên FE → BE → LLM không
- Reproduce được conversation từ log không

9. Chaos / Failure test

Cố tình làm mọi thứ hỏng:
- LLM timeout
- Tool trả 500
- Vector DB down
- Partial response

👉 Chatbot có:
- Retry hợp lý?
- Fallback?
- Thông báo user rõ ràng?
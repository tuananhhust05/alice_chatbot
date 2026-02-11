# Test Coverage - Frontend

## Tính năng đang được test

### 1. API Handlers (handlers.ts)

| API | Tính năng |
|-----|-----------|
| `POST /api/auth/google` | Đăng nhập Google |
| `GET /api/auth/me` | Lấy thông tin user hiện tại |
| `POST /api/auth/logout` | Đăng xuất |
| `GET /api/chat/conversations` | Danh sách conversations |
| `GET /api/chat/conversations/:id` | Chi tiết conversation |
| `POST /api/chat/send` | Gửi tin nhắn |
| `DELETE /api/chat/conversations/:id` | Xóa conversation |
| `GET /api/stream` | Polling response từ LLM |
| `POST /api/files/extract` | Upload và extract nội dung file |

### 2. Error Cases (errorHandlers)

| Error | Mô tả |
|-------|-------|
| `authError` | 401 Unauthorized |
| `networkError` | Network failure |
| `serverError` | 500 Internal Server Error |
| `rateLimitError` | 429 Rate Limit |

### 3. Mock Data Factories (factories.ts)

| Factory | Tạo mock cho |
|---------|--------------|
| `createMockUser` | User object |
| `createMockMessage` | Message (user/assistant) |
| `createMockConversation` | Conversation list item |
| `createMockConversationDetail` | Conversation với messages |

### 4. Browser APIs Mock (setup.ts)

| API | Lý do mock |
|-----|------------|
| `matchMedia` | Responsive design |
| `IntersectionObserver` | Lazy loading |
| `scrollIntoView` | Auto-scroll chat |

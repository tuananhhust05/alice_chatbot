# Giải Thích Cơ Chế Chạy Test Frontend

## Tổng Quan

Folder `test` chứa các file cấu hình để chạy unit test cho frontend. Hệ thống sử dụng:

- **Vitest**: Framework chạy test (tương tự Jest nhưng nhanh hơn, tích hợp tốt với Vite)
- **MSW (Mock Service Worker)**: Thư viện giả lập API calls
- **Testing Library**: Thư viện test React components

## Các File và Chức Năng

### 1. `server.ts` - Khởi tạo Mock Server

```typescript
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

**Chức năng:**
- Tạo một "server giả" chạy trong Node.js
- Server này sẽ chặn (intercept) tất cả HTTP requests từ code test
- Thay vì gọi API thật, requests sẽ được xử lý bởi các handlers đã định nghĩa

---

### 2. `handlers.ts` - Định Nghĩa API Responses Giả

File này định nghĩa các mock responses cho từng API endpoint.

**Cấu trúc:**

```typescript
import { http, HttpResponse } from 'msw';

const API_URL = 'http://localhost:8009';

export const handlers = [
  // Khi có request POST đến /api/auth/google
  http.post(`${API_URL}/api/auth/google`, () => {
    return HttpResponse.json(mockUser);  // Trả về data giả
  }),

  // Khi có request GET đến /api/auth/me
  http.get(`${API_URL}/api/auth/me`, () => {
    return HttpResponse.json(mockUser);
  }),

  // ... các handlers khác
];
```

**Giải thích:**
- `http.get()`, `http.post()`, `http.delete()`: Định nghĩa handler cho từng HTTP method
- `HttpResponse.json()`: Trả về JSON response
- Có thể truy cập params, request body để tạo response động

**Error Handlers:**
```typescript
export const errorHandlers = {
  authError: http.get(`${API_URL}/api/auth/me`, () => {
    return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 });
  }),
  // ...
};
```
- Dùng để test các trường hợp lỗi (401, 500, network error, etc.)

---

### 3. `setup.ts` - Cấu Hình Chạy Trước Mỗi Test

```typescript
import '@testing-library/jest-dom';
import { server } from './server';

// Chạy TRƯỚC TẤT CẢ tests
beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }));

// Chạy SAU MỖI test
afterEach(() => server.resetHandlers());

// Chạy SAU TẤT CẢ tests
afterAll(() => server.close());
```

**Luồng chạy:**

```
┌─────────────────────────────────────────────────────────┐
│                    KHỞI ĐỘNG TEST                        │
├─────────────────────────────────────────────────────────┤
│  beforeAll() → server.listen()                          │
│  (Bật mock server, bắt đầu chặn HTTP requests)          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Test 1 chạy                                      │   │
│  │   → Component gọi API                            │   │
│  │   → MSW chặn request                             │   │
│  │   → Trả về mock data                             │   │
│  │   → Test kiểm tra kết quả                        │   │
│  └─────────────────────────────────────────────────┘   │
│                         ↓                               │
│  afterEach() → server.resetHandlers()                   │
│  (Reset handlers về trạng thái ban đầu)                 │
│                         ↓                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Test 2 chạy                                      │   │
│  │   → ...                                          │   │
│  └─────────────────────────────────────────────────┘   │
│                         ↓                               │
│  afterEach() → server.resetHandlers()                   │
│                         ↓                               │
│  ... (tiếp tục với các tests khác)                      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  afterAll() → server.close()                            │
│  (Tắt mock server)                                      │
└─────────────────────────────────────────────────────────┘
```

**Các Mock bổ sung:**
```typescript
// Mock matchMedia (dùng cho responsive design)
Object.defineProperty(window, 'matchMedia', { ... });

// Mock IntersectionObserver (dùng cho lazy loading, infinite scroll)
Object.defineProperty(window, 'IntersectionObserver', { ... });

// Mock scrollIntoView (dùng cho auto-scroll)
Element.prototype.scrollIntoView = vi.fn();
```

Các mock này cần thiết vì jsdom (môi trường test) không hỗ trợ đầy đủ các browser APIs.

---

### 4. `factories.ts` - Factory Functions Tạo Mock Data

```typescript
export const createMockUser = (overrides: Partial<User> = {}): User => ({
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User',
  picture: 'https://example.com/avatar.jpg',
  ...overrides,  // Cho phép override các giá trị mặc định
});

export const createMockMessage = (overrides: Partial<Message> = {}): Message => ({
  role: 'user',
  content: 'Hello, world!',
  timestamp: new Date().toISOString(),
  ...overrides,
});
```

**Cách sử dụng trong test:**
```typescript
// Tạo user với giá trị mặc định
const user = createMockUser();

// Tạo user với email custom
const adminUser = createMockUser({ email: 'admin@example.com' });

// Tạo message assistant
const botMessage = createMockMessage({ 
  role: 'assistant', 
  content: 'Xin chào!' 
});
```

**Lợi ích:**
- Code test ngắn gọn, dễ đọc
- Dễ dàng tạo variations của data
- Thay đổi cấu trúc data ở một chỗ, tự động cập nhật tất cả tests

---

## Ví Dụ Một Test Hoàn Chỉnh

```typescript
// auth.test.ts
import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context/AuthContext';

describe('AuthContext', () => {
  it('should fetch current user on mount', async () => {
    // 1. Render component
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // 2. Component gọi GET /api/auth/me
    //    → MSW chặn request
    //    → Trả về mockUser từ handlers.ts

    // 3. Kiểm tra kết quả
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });
  });
});
```

---

## Cách Thêm Test Mới

### Bước 1: Thêm handler nếu cần API mới
```typescript
// handlers.ts
http.get(`${API_URL}/api/new-endpoint`, () => {
  return HttpResponse.json({ data: 'value' });
}),
```

### Bước 2: Thêm factory nếu cần data type mới
```typescript
// factories.ts
export const createMockNewType = (overrides = {}) => ({
  field1: 'default',
  field2: 123,
  ...overrides,
});
```

### Bước 3: Viết test
```typescript
// NewComponent.test.tsx
import { createMockNewType } from '../test/factories';

describe('NewComponent', () => {
  it('should render correctly', () => {
    const data = createMockNewType({ field1: 'custom' });
    render(<NewComponent data={data} />);
    expect(screen.getByText('custom')).toBeInTheDocument();
  });
});
```

---

## Tóm Tắt

| File | Chức năng |
|------|-----------|
| `server.ts` | Tạo mock server từ MSW |
| `handlers.ts` | Định nghĩa responses cho từng API endpoint |
| `setup.ts` | Cấu hình lifecycle (beforeAll, afterEach, afterAll) và mock browser APIs |
| `factories.ts` | Helper functions tạo mock data nhanh |

**Luồng hoạt động:**
1. Vitest load `setup.ts` trước khi chạy tests
2. Mock server được bật lên
3. Mỗi test chạy, các API calls bị chặn và trả về mock data
4. Sau mỗi test, handlers được reset
5. Sau tất cả tests, server được tắt

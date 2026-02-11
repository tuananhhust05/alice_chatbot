import { http, HttpResponse } from 'msw';

const API_URL = 'http://localhost:8000';

// Mock data
const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User',
  picture: 'https://example.com/avatar.jpg',
};

const mockConversations = [
  {
    id: 'conv-1',
    title: 'First conversation',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    message_count: 2,
  },
  {
    id: 'conv-2',
    title: 'Second conversation',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    message_count: 4,
  },
];

const mockConversationDetail = {
  id: 'conv-1',
  title: 'First conversation',
  messages: [
    { role: 'user', content: 'Hello', timestamp: '2024-01-01T00:00:00Z' },
    { role: 'assistant', content: 'Hi there!', timestamp: '2024-01-01T00:00:01Z' },
  ],
  file_ids: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const handlers = [
  // Auth handlers
  http.post(`${API_URL}/api/auth/google`, () => {
    return HttpResponse.json(mockUser);
  }),

  http.get(`${API_URL}/api/auth/me`, () => {
    return HttpResponse.json(mockUser);
  }),

  http.post(`${API_URL}/api/auth/logout`, () => {
    return HttpResponse.json({ message: 'Logged out' });
  }),

  // Chat handlers
  http.get(`${API_URL}/api/chat/conversations`, () => {
    return HttpResponse.json(mockConversations);
  }),

  http.get(`${API_URL}/api/chat/conversations/:id`, ({ params }) => {
    if (params.id === 'not-found') {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    }
    return HttpResponse.json({ ...mockConversationDetail, id: params.id });
  }),

  http.post(`${API_URL}/api/chat/send`, async ({ request }) => {
    const body = await request.json() as { message: string };
    return HttpResponse.json({
      request_id: 'req-123',
      conversation_id: 'conv-new',
    });
  }),

  http.delete(`${API_URL}/api/chat/conversations/:id`, () => {
    return HttpResponse.json({ message: 'Deleted' });
  }),

  // Stream handler
  http.get(`${API_URL}/api/stream`, ({ request }) => {
    const url = new URL(request.url);
    const requestId = url.searchParams.get('request_id');
    
    return HttpResponse.json({
      status: 'completed',
      reply: 'This is the AI response',
      title: 'New Title',
      finished: 1,
    });
  }),

  // File extract handler
  http.post(`${API_URL}/api/files/extract`, async () => {
    return HttpResponse.json({
      text: 'Extracted text content',
      original_name: 'test.pdf',
      file_type: 'pdf',
      file_size: 1024,
      text_length: 22,
      text_truncated: false,
    });
  }),
];

// Error handlers for testing error cases
export const errorHandlers = {
  authError: http.get(`${API_URL}/api/auth/me`, () => {
    return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 });
  }),

  networkError: http.get(`${API_URL}/api/chat/conversations`, () => {
    return HttpResponse.error();
  }),

  serverError: http.post(`${API_URL}/api/chat/send`, () => {
    return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }),

  rateLimitError: http.post(`${API_URL}/api/chat/send`, () => {
    return HttpResponse.json({ detail: 'Rate limit exceeded' }, { status: 429 });
  }),
};

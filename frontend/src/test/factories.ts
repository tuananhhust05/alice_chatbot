/**
 * Test utilities - mock data factories
 */
import { User, Message, Conversation, ConversationDetail } from '../types';

export const createMockUser = (overrides: Partial<User> = {}): User => ({
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User',
  picture: 'https://example.com/avatar.jpg',
  ...overrides,
});

export const createMockMessage = (overrides: Partial<Message> = {}): Message => ({
  role: 'user',
  content: 'Hello, world!',
  timestamp: new Date().toISOString(),
  ...overrides,
});

export const createMockConversation = (overrides: Partial<Conversation> = {}): Conversation => ({
  id: 'conv-123',
  title: 'Test Conversation',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  message_count: 2,
  ...overrides,
});

export const createMockConversationDetail = (
  overrides: Partial<ConversationDetail> = {}
): ConversationDetail => ({
  id: 'conv-123',
  title: 'Test Conversation',
  messages: [
    createMockMessage({ role: 'user', content: 'Hello' }),
    createMockMessage({ role: 'assistant', content: 'Hi there!' }),
  ],
  file_ids: [],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

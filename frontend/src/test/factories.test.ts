import { describe, it, expect } from 'vitest';
import { 
  createMockUser, 
  createMockMessage, 
  createMockConversation,
  createMockConversationDetail 
} from './factories';

describe('Test Factories', () => {
  describe('createMockUser', () => {
    it('should create user with default values', () => {
      const user = createMockUser();

      expect(user.id).toBe('user-123');
      expect(user.email).toBe('test@example.com');
      expect(user.name).toBe('Test User');
    });

    it('should allow overriding values', () => {
      const user = createMockUser({ name: 'Custom Name' });

      expect(user.name).toBe('Custom Name');
      expect(user.email).toBe('test@example.com'); // Default preserved
    });
  });

  describe('createMockMessage', () => {
    it('should create message with default values', () => {
      const message = createMockMessage();

      expect(message.role).toBe('user');
      expect(message.content).toBe('Hello, world!');
      expect(message.timestamp).toBeDefined();
    });

    it('should allow overriding role', () => {
      const message = createMockMessage({ role: 'assistant' });

      expect(message.role).toBe('assistant');
    });
  });

  describe('createMockConversation', () => {
    it('should create conversation with default values', () => {
      const conv = createMockConversation();

      expect(conv.id).toBe('conv-123');
      expect(conv.title).toBe('Test Conversation');
      expect(conv.message_count).toBe(2);
    });
  });

  describe('createMockConversationDetail', () => {
    it('should create conversation detail with messages', () => {
      const detail = createMockConversationDetail();

      expect(detail.id).toBe('conv-123');
      expect(detail.messages).toHaveLength(2);
      expect(detail.messages[0].role).toBe('user');
      expect(detail.messages[1].role).toBe('assistant');
    });
  });
});

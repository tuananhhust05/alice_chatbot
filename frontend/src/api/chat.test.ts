import { describe, it, expect, beforeEach } from 'vitest';
import { server } from '../test/server';
import { errorHandlers } from '../test/handlers';
import {
  sendMessage,
  pollStream,
  getConversations,
  getConversation,
  deleteConversation,
} from './chat';

describe('Chat API', () => {
  describe('sendMessage', () => {
    it('should send message and return request_id', async () => {
      const result = await sendMessage({
        message: 'Hello, AI!',
      });

      expect(result).toHaveProperty('request_id');
      expect(result).toHaveProperty('conversation_id');
      expect(result.request_id).toBe('req-123');
      expect(result.conversation_id).toBe('conv-new');
    });

    it('should include conversation_id when provided', async () => {
      const result = await sendMessage({
        message: 'Hello',
        conversationId: 'existing-conv',
      });

      expect(result.request_id).toBe('req-123');
    });

    it('should include display_content when provided', async () => {
      const result = await sendMessage({
        message: 'Full message with file content',
        displayContent: '[Attached: file.pdf]\n\nShort message',
      });

      expect(result.request_id).toBe('req-123');
    });
  });

  describe('pollStream', () => {
    it('should return stream response', async () => {
      const result = await pollStream('req-123');

      expect(result.status).toBe('completed');
      expect(result.reply).toBe('This is the AI response');
      expect(result.finished).toBe(1);
    });

    it('should include title when available', async () => {
      const result = await pollStream('req-123');

      expect(result.title).toBe('New Title');
    });
  });

  describe('getConversations', () => {
    it('should return list of conversations', async () => {
      const conversations = await getConversations();

      expect(conversations).toHaveLength(2);
      expect(conversations[0]).toHaveProperty('id');
      expect(conversations[0]).toHaveProperty('title');
      expect(conversations[0]).toHaveProperty('message_count');
    });

    it('should include all required fields', async () => {
      const conversations = await getConversations();
      const conv = conversations[0];

      expect(conv.id).toBe('conv-1');
      expect(conv.title).toBe('First conversation');
      expect(conv.message_count).toBe(2);
      expect(conv.created_at).toBeDefined();
      expect(conv.updated_at).toBeDefined();
    });
  });

  describe('getConversation', () => {
    it('should return conversation detail', async () => {
      const detail = await getConversation('conv-1');

      expect(detail.id).toBe('conv-1');
      expect(detail.title).toBe('First conversation');
      expect(detail.messages).toHaveLength(2);
    });

    it('should include messages with correct structure', async () => {
      const detail = await getConversation('conv-1');
      const message = detail.messages[0];

      expect(message).toHaveProperty('role');
      expect(message).toHaveProperty('content');
      expect(message).toHaveProperty('timestamp');
      expect(message.role).toBe('user');
    });

    it('should throw error for non-existent conversation', async () => {
      await expect(getConversation('not-found')).rejects.toThrow();
    });
  });

  describe('deleteConversation', () => {
    it('should delete conversation successfully', async () => {
      await expect(deleteConversation('conv-1')).resolves.toBeUndefined();
    });
  });
});

describe('Chat API Error Handling', () => {
  it('should handle server errors', async () => {
    server.use(errorHandlers.serverError);

    await expect(
      sendMessage({ message: 'Hello' })
    ).rejects.toThrow();
  });

  it('should handle rate limit errors', async () => {
    server.use(errorHandlers.rateLimitError);

    await expect(
      sendMessage({ message: 'Hello' })
    ).rejects.toThrow();
  });

  it('should handle network errors', async () => {
    server.use(errorHandlers.networkError);

    await expect(getConversations()).rejects.toThrow();
  });
});

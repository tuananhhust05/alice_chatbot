import api from './client';
import { SendResponse, StreamResponse, Conversation, ConversationDetail } from '../types';

export interface SendMessageOptions {
  message: string;          // Full message with file content (for LLM)
  displayContent?: string;  // Short version for UI display
  conversationId?: string;
}

export const sendMessage = async (options: SendMessageOptions): Promise<SendResponse> => {
  const { data } = await api.post('/api/chat/send', {
    message: options.message,
    display_content: options.displayContent,
    conversation_id: options.conversationId,
  });
  return data;
};

export const pollStream = async (requestId: string): Promise<StreamResponse> => {
  const { data } = await api.get(`/api/stream`, {
    params: { request_id: requestId },
  });
  return data;
};

export const getConversations = async (): Promise<Conversation[]> => {
  const { data } = await api.get('/api/chat/conversations');
  return data;
};

export const getConversation = async (id: string): Promise<ConversationDetail> => {
  const { data } = await api.get(`/api/chat/conversations/${id}`);
  return data;
};

export const deleteConversation = async (id: string): Promise<void> => {
  await api.delete(`/api/chat/conversations/${id}`);
};

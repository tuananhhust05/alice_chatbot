export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationDetail {
  id: string;
  title: string;
  messages: Message[];
  file_ids: string[];
  created_at: string;
  updated_at: string;
}

// POST /api/chat/send
export interface SendResponse {
  request_id: string;
  conversation_id: string;
}

// POST /api/files/extract — extract text from file
export interface FileExtractResponse {
  text: string;
  original_name: string;
  file_type: string;
  file_size: number;
  text_length: number;
  text_truncated: boolean;
}

// GET /api/stream?request_id=xxx
export interface StreamResponse {
  status: 'processing' | 'streaming' | 'completed' | 'error';
  reply?: string;
  title?: string;
  finished: number; // 0 = not done, 1 = done
  error?: string;
}

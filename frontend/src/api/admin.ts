import api from './client';

// ===== Auth =====
export const adminLogin = async (username: string, password: string) => {
  const { data } = await api.post('/api/admin/login', { username, password });
  return data;
};

export const adminLogout = async () => {
  await api.post('/api/admin/logout');
};

export const adminMe = async () => {
  const { data } = await api.get('/api/admin/me');
  return data;
};

// ===== Users =====
export const getUsers = async (skip = 0, limit = 50) => {
  const { data } = await api.get('/api/admin/users', { params: { skip, limit } });
  return data;
};

export const deleteUser = async (userId: string) => {
  await api.delete(`/api/admin/users/${userId}`);
};

// ===== Conversations =====
export const getAdminConversations = async (skip = 0, limit = 50, userEmail?: string) => {
  const { data } = await api.get('/api/admin/conversations', {
    params: { skip, limit, user_email: userEmail },
  });
  return data;
};

export const getAdminConversationDetail = async (id: string) => {
  const { data } = await api.get(`/api/admin/conversations/${id}`);
  return data;
};

export const deleteAdminConversation = async (id: string) => {
  await api.delete(`/api/admin/conversations/${id}`);
};

// ===== Analytics =====
export const getAnalyticsOverview = async () => {
  const { data } = await api.get('/api/admin/analytics/overview');
  return data;
};

export const getAnalyticsMetrics = async (metric?: string, limit = 50) => {
  const { data } = await api.get('/api/admin/analytics/metrics', {
    params: { metric, limit },
  });
  return data;
};

export const getAnalyticsEvents = async (eventType?: string, skip = 0, limit = 50) => {
  const { data } = await api.get('/api/admin/analytics/events', {
    params: { event_type: eventType, skip, limit },
  });
  return data;
};

export const getAnalyticsTimeseries = async (series?: string, limit = 100) => {
  const { data } = await api.get('/api/admin/analytics/timeseries', {
    params: { series, limit },
  });
  return data;
};

// ===== Prompts =====
export const getPrompts = async () => {
  const { data } = await api.get('/api/admin/prompts');
  return data;
};

export const updatePrompts = async (systemPrompt: string, ragPromptTemplate: string) => {
  const { data } = await api.put('/api/admin/prompts', {
    system_prompt: systemPrompt,
    rag_prompt_template: ragPromptTemplate,
  });
  return data;
};

// ===== RAG Data =====
export const getRagData = async (skip = 0, limit = 50) => {
  const { data } = await api.get('/api/admin/ragdata', { params: { skip, limit } });
  return data;
};

export const uploadRagData = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/api/admin/ragdata/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const deleteRagData = async (recordId: string) => {
  await api.delete(`/api/admin/ragdata/${recordId}`);
};

// ===== IP Management =====
export interface IPStatsResponse {
  ips: Array<{
    ip: string;
    total_requests: number;
    days: Record<string, number>;
  }>;
  total: number;
  date_from: string;
  date_to: string;
}

export interface IPSummaryResponse {
  ip_activity: Array<{
    ip: string;
    message_count: number;
    unique_users_count: number;
    last_activity: string;
  }>;
  blacklisted_ips: string[];
  total_messages_today: number;
  unique_ips_today: number;
}

export interface IPMessagesResponse {
  messages: Array<{
    id: string;
    ip: string;
    user_id: string;
    conversation_id: string;
    message_preview: string;
    timestamp: string;
  }>;
  total: number;
  skip: number;
  limit: number;
}

export const getIPStats = async (
  dateFrom?: string,
  dateTo?: string,
  ipFilter?: string,
  limit = 100
): Promise<IPStatsResponse> => {
  const { data } = await api.get('/api/admin/ip/stats', {
    params: { date_from: dateFrom, date_to: dateTo, ip_filter: ipFilter, limit },
  });
  return data;
};

export const getIPSummary = async (): Promise<IPSummaryResponse> => {
  const { data } = await api.get('/api/admin/ip/summary');
  return data;
};

export const getIPMessages = async (
  ip?: string,
  dateFrom?: string,
  dateTo?: string,
  skip = 0,
  limit = 50
): Promise<IPMessagesResponse> => {
  const { data } = await api.get('/api/admin/ip/messages', {
    params: { ip, date_from: dateFrom, date_to: dateTo, skip, limit },
  });
  return data;
};

export const getIPBlacklist = async (): Promise<{ blacklisted_ips: string[]; total: number }> => {
  const { data } = await api.get('/api/admin/ip/blacklist');
  return data;
};

export const blacklistIP = async (
  ip: string,
  reason?: string,
  ttlHours?: number
): Promise<{ message: string; ip: string }> => {
  const { data } = await api.post('/api/admin/ip/blacklist', {
    ip,
    reason,
    ttl_hours: ttlHours,
  });
  return data;
};

export const unblacklistIP = async (ip: string): Promise<{ message: string; ip: string }> => {
  const { data } = await api.delete(`/api/admin/ip/blacklist/${encodeURIComponent(ip)}`);
  return data;
};

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

// ===== Dead Letter Queue =====
export interface DLQTask {
  id: string;
  job_id: string;
  task_type: string;
  status: string;
  retry_count: number;
  max_retry: number;
  error_message: string;
  error_type: string;
  original_payload: Record<string, unknown>;
  failed_at: string;
  created_at: string;
  last_retry_at: string;
}

export interface DLQTaskDetail extends DLQTask {
  error_stack_trace: string;
  retry_history: Array<{
    attempt: number;
    requested_at: string;
    requested_by: string;
    type: string;
  }>;
  metadata: Record<string, unknown>;
}

export interface DLQListResponse {
  tasks: DLQTask[];
  total: number;
  skip: number;
  limit: number;
}

export interface DLQSummaryResponse {
  total: number;
  pending_retry: number;
  recent_failures_24h: number;
  by_status: Record<string, number>;
  by_task_type: Record<string, number>;
  by_error_type: Record<string, number>;
}

export interface DLQActionResponse {
  message: string;
  retried?: string[];
  deleted?: string[];
  failed?: Array<{ id: string; reason: string }>;
}

export const getDLQTasks = async (
  status?: string,
  taskType?: string,
  dateFrom?: string,
  dateTo?: string,
  skip = 0,
  limit = 50
): Promise<DLQListResponse> => {
  const { data } = await api.get('/api/admin/dlq', {
    params: { status, task_type: taskType, date_from: dateFrom, date_to: dateTo, skip, limit },
  });
  return data;
};

export const getDLQSummary = async (): Promise<DLQSummaryResponse> => {
  const { data } = await api.get('/api/admin/dlq/summary');
  return data;
};

export const getDLQTaskDetail = async (taskId: string): Promise<DLQTaskDetail> => {
  const { data } = await api.get(`/api/admin/dlq/${taskId}`);
  return data;
};

export const retryDLQTasks = async (taskIds: string[]): Promise<DLQActionResponse> => {
  const { data } = await api.post('/api/admin/dlq/retry', { task_ids: taskIds });
  return data;
};

export const deleteDLQTasks = async (taskIds: string[]): Promise<DLQActionResponse> => {
  const { data } = await api.post('/api/admin/dlq/delete', { task_ids: taskIds });
  return data;
};

export const clearDLQ = async (
  status?: string,
  olderThanDays?: number
): Promise<{ message: string; deleted_count: number }> => {
  const { data } = await api.delete('/api/admin/dlq/clear', {
    params: { status, older_than_days: olderThanDays },
  });
  return data;
};

export const exportDLQTasks = async (
  status?: string,
  taskType?: string,
  limit = 1000
): Promise<{ exported_at: string; total_exported: number; tasks: DLQTask[] }> => {
  const { data } = await api.get('/api/admin/dlq/export', {
    params: { status, task_type: taskType, limit },
  });
  return data;
};

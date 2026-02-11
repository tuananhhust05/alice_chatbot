/**
 * Utility functions for chat operations.
 * Extracted for easier testing.
 */

/**
 * Parse attached file info from message content.
 * Format: "[Attached: filename.ext]\n\nActual message"
 */
export const parseAttachedFile = (
  content: string
): { fileName: string | null; displayContent: string } => {
  const attachedMatch = content.match(/^\[Attached: (.+?)\]\n\n/);
  if (attachedMatch) {
    return {
      fileName: attachedMatch[1],
      displayContent: content.replace(attachedMatch[0], ''),
    };
  }
  return { fileName: null, displayContent: content };
};

/**
 * Build actual message with file content for sending to LLM.
 * Format: "user text\n\nFile content:\n[File: filename]\nfile text"
 */
export const buildActualMessage = (
  userText: string,
  attachedFile: { name: string; text: string } | null
): string => {
  if (!attachedFile) {
    return userText || '';
  }

  const fileLabel = `[File: ${attachedFile.name}]`;
  const messageText = userText || 'Please analyze this file.';
  
  return `${messageText}\n\nFile content:\n${fileLabel}\n${attachedFile.text}`;
};

/**
 * Build display content for UI (shorter version without file content).
 * Format: "[Attached: filename]\n\nuser text"
 */
export const buildDisplayContent = (
  userText: string,
  attachedFile: { name: string } | null
): string => {
  if (!attachedFile) {
    return userText;
  }

  const displayText = userText || 'Please analyze this file.';
  return `[Attached: ${attachedFile.name}]\n\n${displayText}`;
};

/**
 * Format file size for display.
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/**
 * Validate file type is supported.
 */
export const SUPPORTED_FILE_TYPES = ['pdf', 'txt', 'csv', 'docx', 'xlsx'];

export const isValidFileType = (filename: string): boolean => {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  return SUPPORTED_FILE_TYPES.includes(ext);
};

/**
 * Get file extension from filename.
 */
export const getFileExtension = (filename: string): string => {
  const parts = filename.split('.');
  // If no dot or only one part (no extension), return empty string
  if (parts.length <= 1) {
    return '';
  }
  return parts.pop()?.toLowerCase() || '';
};

/**
 * Truncate text with ellipsis.
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) {
    return text;
  }
  return text.slice(0, maxLength - 3) + '...';
};

/**
 * Format timestamp for display.
 */
export const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) {
    return 'Just now';
  }
  if (diffMins < 60) {
    return `${diffMins}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`;
  }
  return date.toLocaleDateString();
};

/**
 * Validate message is not empty (after trimming).
 */
export const isValidMessage = (message: string): boolean => {
  return message.trim().length > 0;
};

/**
 * Check if content contains file attachment marker.
 */
export const hasFileAttachment = (content: string): boolean => {
  return content.startsWith('[Attached:');
};

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ConversationDetail, Message, FileExtractResponse } from '../types';
import { sendMessage, pollStream } from '../api/chat';
import { extractFileContent } from '../api/files';
import MessageBubble from './MessageBubble';
import StreamingBubble from './StreamingBubble';
import FileUploadButton from './FileUploadButton';
import {
  HiOutlinePaperAirplane,
  HiSparkles,
  HiOutlineDocumentText,
  HiOutlineChatBubbleLeftEllipsis,
  HiOutlineLightBulb,
  HiOutlineXMark,
} from 'react-icons/hi2';

// Track which conversation is currently loaded to avoid overwriting optimistic messages
let syncedConversationId: string | null = null;

interface ChatAreaProps {
  conversation: ConversationDetail | null;
  conversationId: string | null;
  onConversationUpdate: (conversationId: string, message: Message, title?: string) => void;
  onNewConversationCreated: (conversationId: string, messages: Message[], title?: string) => void;
}

interface AttachedFile {
  name: string;
  type: string;
  size: number;
  text: string;
  textTruncated?: boolean;
}

const SUGGESTIONS = [
  { icon: HiOutlineChatBubbleLeftEllipsis, text: "Explain quantum computing in simple terms" },
  { icon: HiOutlineLightBulb, text: "Help me write a professional email" },
  { icon: HiOutlineDocumentText, text: "Summarize a document for me" },
];

const ProcessingIndicator: React.FC = () => (
  <div className="flex items-start gap-4 my-4 px-4 animate-fade-in">
    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#0A84FF] to-[#5E5CE6] flex items-center justify-center flex-shrink-0">
      <HiSparkles className="w-4 h-4 text-white" />
    </div>
    <div className="flex items-center gap-2 py-2">
      <div className="flex items-center gap-1.5">
        <div className="w-2 h-2 rounded-full bg-apple-accent animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-2 h-2 rounded-full bg-apple-accent animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-2 h-2 rounded-full bg-apple-accent animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-sm text-apple-secondary ml-2">Processing...</span>
    </div>
  </div>
);

const ChatArea: React.FC<ChatAreaProps> = ({
  conversation,
  conversationId,
  onConversationUpdate,
  onNewConversationCreated,
}) => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [attachedFile, setAttachedFile] = useState<AttachedFile | null>(null);
  const [isExtractingFile, setIsExtractingFile] = useState(false);
  const [localMessages, setLocalMessages] = useState<Message[]>([]);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync local messages with conversation — only when switching to a different conversation
  useEffect(() => {
    if (conversation) {
      if (syncedConversationId !== conversation.id) {
        setLocalMessages(conversation.messages);
        syncedConversationId = conversation.id;
      }
    } else if (!conversationId) {
      setLocalMessages([]);
      setAttachedFile(null);
      syncedConversationId = null;
    }
  }, [conversation, conversationId]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [localMessages, isLoading, isStreaming, streamingContent]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [input]);

  // Handle file upload — extract text immediately
  const handleFileUpload = useCallback(async (file: File) => {
    if (isLoading || isStreaming || isExtractingFile) return;

    setIsExtractingFile(true);
    setError('');

    try {
      const result: FileExtractResponse = await extractFileContent(file);
      
      setAttachedFile({
        name: result.original_name,
        type: result.file_type,
        size: result.file_size,
        text: result.text,
        textTruncated: result.text_truncated,
      });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to extract file content';
      setError(msg);
    } finally {
      setIsExtractingFile(false);
    }
  }, [isLoading, isStreaming, isExtractingFile]);

  // Remove attached file
  const handleRemoveFile = useCallback(() => {
    setAttachedFile(null);
  }, []);

  // Send message (with optional attached file content)
  const handleSend = useCallback(async (suggestionText?: string) => {
    const messageText = suggestionText || input.trim();
    if (!messageText && !attachedFile) return;
    if (isLoading || isStreaming) return;

    // Build the actual message to send to API
    // Format: "<text input>\n\nFile content:\n[File: filename]\n<file content>"
    let actualMessage = messageText || 'Please analyze this file.';
    if (attachedFile) {
      const fileLabel = `[File: ${attachedFile.name}]`;
      if (messageText) {
        actualMessage = `${messageText}\n\nFile content:\n${fileLabel}\n${attachedFile.text}`;
      } else {
        actualMessage = `Please analyze this file.\n\nFile content:\n${fileLabel}\n${attachedFile.text}`;
      }
    }

    // Build display message (what user sees in UI - shorter version)
    let displayContent = messageText;
    if (attachedFile && messageText) {
      displayContent = `[Attached: ${attachedFile.name}]\n\n${messageText}`;
    } else if (attachedFile && !messageText) {
      displayContent = `[Attached: ${attachedFile.name}]\n\nPlease analyze this file.`;
    }

    const userMessage: Message = {
      role: 'user',
      content: displayContent,
      timestamp: new Date().toISOString(),
    };

    // Optimistic update
    setLocalMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError('');
    setStreamingContent('');
    setAttachedFile(null);

    try {
      // Send to backend:
      // - message: full content with file (for LLM)
      // - displayContent: short version (saved to DB for UI)
      const sendResp = await sendMessage({
        message: actualMessage,
        displayContent: displayContent,
        conversationId: conversationId || undefined,
      });

      // Poll for streaming response
      const maxAttempts = 300;
      let attempts = 0;
      let lastContent = '';

      await new Promise((r) => setTimeout(r, 100));

      while (attempts < maxAttempts) {
        const streamData = await pollStream(sendResp.request_id);

        if (streamData.status === 'error') {
          throw new Error(streamData.error || 'Processing failed');
        }

        if (streamData.reply && streamData.reply !== lastContent) {
          lastContent = streamData.reply;
          setStreamingContent(lastContent);
          if (!isStreaming) setIsStreaming(true);
        }

        if (streamData.finished === 1) {
          const assistantMessage: Message = {
            role: 'assistant',
            content: streamData.reply || '',
            timestamp: new Date().toISOString(),
          };

          setLocalMessages((prev) => [...prev, assistantMessage]);

          if (!conversationId) {
            onNewConversationCreated(
              sendResp.conversation_id,
              [userMessage, assistantMessage],
              streamData.title
            );
          } else {
            onConversationUpdate(sendResp.conversation_id, assistantMessage, streamData.title);
          }
          break;
        }

        attempts++;
        await new Promise((r) => setTimeout(r, 100));
      }

      if (attempts >= maxAttempts) {
        throw new Error('Response timeout');
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to send message';
      setError(msg);
      // Remove optimistic message on error
      setLocalMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamingContent('');
    }
  }, [input, attachedFile, conversationId, isLoading, isStreaming, onConversationUpdate, onNewConversationCreated]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    if (isLoading || isStreaming || isExtractingFile) return;

    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          e.preventDefault();
          handleFileUpload(file);
          break;
        }
      }
    }
  };

  const hasMessages = localMessages.length > 0;
  const canSend = (input.trim() || attachedFile) && !isLoading && !isStreaming && !isExtractingFile;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative z-10">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {!hasMessages ? (
          /* Empty state */
          <div className="h-full flex flex-col items-center justify-center px-4 pt-14 lg:pt-4">
            <div className="text-center mb-6 sm:mb-8 animate-fade-in">
              <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-[#0A84FF] via-[#5E5CE6] to-[#BF5AF2] flex items-center justify-center mx-auto mb-4 shadow-lg shadow-purple-500/30 star-pulse">
                <HiSparkles className="w-7 h-7 sm:w-8 sm:h-8 text-white" />
              </div>
              <h1 className="text-xl sm:text-2xl font-semibold text-white mb-2">Hello! I'm Alice</h1>
              <p className="text-apple-secondary text-sm">Your cosmic AI assistant</p>
            </div>

            <div className="w-full max-w-2xl space-y-2 px-2 sm:px-0">
              {SUGGESTIONS.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSend(suggestion.text)}
                  disabled={isLoading || isStreaming}
                  className="w-full flex items-center gap-3 px-3 sm:px-4 py-3 rounded-xl space-glass cosmic-glow border border-white/10 hover:border-white/20 transition-all duration-300 group text-left touch-target"
                >
                  <suggestion.icon className="w-5 h-5 text-apple-accent flex-shrink-0" />
                  <span className="text-sm text-apple-secondary group-hover:text-white transition-colors line-clamp-2">
                    {suggestion.text}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Messages */
          <div className="max-w-3xl mx-auto w-full px-3 sm:px-4 py-4 sm:py-6 pt-14 lg:pt-6">
            {localMessages.map((msg, index) => (
              <MessageBubble key={index} message={msg} />
            ))}
            {isLoading && !isStreaming && <ProcessingIndicator />}
            {isStreaming && streamingContent && (
              <StreamingBubble content={streamingContent} />
            )}
            {error && (
              <div className="flex justify-center my-4 animate-fade-in">
                <div className="px-4 py-2 rounded-xl bg-apple-red/10 border border-apple-red/20 text-apple-red text-sm">
                  {error}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="bg-transparent pb-3 pt-2 safe-area-bottom relative z-20">
        <div className="max-w-3xl mx-auto w-full px-3 sm:px-4">
          {/* Unified input container - Space themed */}
          <div className="relative rounded-2xl sm:rounded-3xl space-glass border border-white/15 focus-within:border-purple-500/50 transition-all duration-300 focus-within:shadow-[0_0_30px_rgba(94,92,230,0.3)]">
            {/* Attached file indicator */}
            {attachedFile && (
              <div className="flex items-center gap-2 mx-2 sm:mx-3 mt-2 sm:mt-3 mb-0 px-2 sm:px-3 py-2 rounded-lg sm:rounded-xl bg-apple-accent/10 text-apple-accent text-xs">
                <HiOutlineDocumentText className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="truncate flex-1 max-w-[120px] sm:max-w-none">{attachedFile.name}</span>
                <span className="text-apple-tertiary hidden sm:inline">
                  {(attachedFile.size / 1024).toFixed(1)} KB
                </span>
                {attachedFile.textTruncated && (
                  <span className="text-yellow-400 text-[10px] hidden sm:inline">(truncated)</span>
                )}
                <button
                  onClick={handleRemoveFile}
                  className="p-1 hover:bg-apple-accent/20 rounded transition-colors touch-target flex items-center justify-center"
                >
                  <HiOutlineXMark className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Extracting file indicator */}
            {isExtractingFile && (
              <div className="flex items-center gap-2 mx-2 sm:mx-3 mt-2 sm:mt-3 mb-0 px-2 sm:px-3 py-2 rounded-lg sm:rounded-xl bg-apple-elevated text-apple-secondary text-xs">
                <div className="w-3 h-3 border-2 border-apple-accent border-t-transparent rounded-full animate-spin" />
                <span>Extracting file content...</span>
              </div>
            )}

            {/* Textarea row */}
            <div className="flex items-end gap-1 px-2 py-2">
              {/* Attach button */}
              <FileUploadButton 
                onFileSelect={handleFileUpload} 
                disabled={isLoading || isStreaming || isExtractingFile} 
              />

              {/* Textarea */}
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onPaste={handlePaste}
                placeholder={attachedFile ? "Add a message or send directly" : "Ask anything"}
                rows={1}
                disabled={isLoading || isStreaming}
                className="flex-1 resize-none bg-transparent text-sm sm:text-base text-white placeholder-apple-tertiary focus:outline-none disabled:opacity-50 py-2 px-1 leading-6 overflow-hidden mobile-input"
                style={{ maxHeight: '150px' }}
              />

              {/* Send button */}
              <button
                onClick={() => handleSend()}
                disabled={!canSend}
                className={`
                  flex-shrink-0 w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center rounded-full mb-0.5
                  transition-all duration-300 touch-target
                  ${canSend
                    ? 'bg-gradient-to-r from-[#0A84FF] via-[#5E5CE6] to-[#BF5AF2] text-white hover:shadow-[0_0_20px_rgba(94,92,230,0.5)] scale-100'
                    : 'bg-white/10 text-apple-tertiary scale-95 opacity-50'
                  }
                `}
              >
                <HiOutlinePaperAirplane className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
            </div>
          </div>

          <p className="text-center text-[10px] sm:text-[11px] text-apple-tertiary mt-2">
            Alice can make mistakes. Consider checking important information.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;

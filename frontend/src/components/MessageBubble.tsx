import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '../types';
import { HiSparkles, HiUser, HiOutlineDocumentText } from 'react-icons/hi2';
import CodeBlock from './CodeBlock';
import { parseAttachedFile } from '../utils/chat';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const { fileName, displayContent } = parseAttachedFile(message.content);

  return (
    <div 
      className={`flex gap-3 mb-6 animate-slide-up ${isUser ? 'flex-row-reverse' : ''}`}
      data-testid={`message-bubble-${message.role}`}
    >
      {/* Avatar */}
      <div className={`
        flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center mt-0.5
        ${isUser
          ? 'bg-apple-elevated'
          : 'bg-gradient-to-br from-[#0A84FF] to-[#5E5CE6]'
        }
      `}>
        {isUser ? (
          <HiUser className="w-4 h-4 text-apple-secondary" data-testid="user-avatar" />
        ) : (
          <HiSparkles className="w-4 h-4 text-white" data-testid="assistant-avatar" />
        )}
      </div>

      {/* Message content */}
      <div className={`
        flex-1 min-w-0
        ${isUser ? 'flex justify-end' : ''}
      `}>
        <div className="max-w-[85%] inline-block">
          {/* File attachment badge for user messages */}
          {isUser && fileName && (
            <div 
              className="flex items-center gap-2 mb-2 px-3 py-1.5 rounded-lg bg-apple-accent/20 text-apple-accent text-xs w-fit ml-auto"
              data-testid="file-attachment-badge"
            >
              <HiOutlineDocumentText className="w-3.5 h-3.5" />
              <span data-testid="attached-file-name">{fileName}</span>
            </div>
          )}

          {/* Message bubble */}
          <div className={`
            rounded-2xl px-4 py-3
            ${isUser
              ? 'bg-apple-accent text-white rounded-tr-md'
              : 'bg-apple-surface glass-border text-white/90 rounded-tl-md'
            }
          `}>
            {isUser ? (
              <p 
                className="text-sm leading-relaxed whitespace-pre-wrap"
                data-testid="user-message-content"
              >
                {displayContent || 'Please analyze this file.'}
              </p>
            ) : (
              <div className="markdown-content text-sm" data-testid="assistant-message-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ node, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      const isInline = !match && !className;
                      if (isInline) {
                        return (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      }
                      return (
                        <CodeBlock
                          language={match ? match[1] : ''}
                          value={String(children).replace(/\n$/, '')}
                        />
                      );
                    },
                    // Render markdown tables with better styling
                    table({ children }) {
                      return (
                        <div className="overflow-x-auto my-2">
                          <table className="min-w-full text-xs border-collapse">
                            {children}
                          </table>
                        </div>
                      );
                    },
                    thead({ children }) {
                      return <thead className="bg-apple-surface/50">{children}</thead>;
                    },
                    th({ children }) {
                      return (
                        <th className="px-3 py-2 text-left text-apple-secondary font-medium border-b border-apple-border">
                          {children}
                        </th>
                      );
                    },
                    td({ children }) {
                      return (
                        <td className="px-3 py-1.5 border-b border-apple-border/50">
                          {children}
                        </td>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;

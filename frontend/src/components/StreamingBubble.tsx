import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { HiSparkles } from 'react-icons/hi2';
import CodeBlock from './CodeBlock';

interface StreamingBubbleProps {
  content: string; // Full accumulated content from server (grows over time)
}

/**
 * StreamingBubble — renders AI response with typewriter effect.
 *
 * How it works:
 * - `content` prop grows over time as server streams (e.g. "Hello" → "Hello world" → "Hello world!")
 * - We maintain `displayedLength` which is how many chars we've "typed" so far
 * - A fast interval types chars from displayedLength up to content.length
 * - When new content arrives (content.length > displayedLength), we seamlessly continue typing
 * - This means: no gap, no re-render flash — just continuous typing
 */
const StreamingBubble: React.FC<StreamingBubbleProps> = ({ content }) => {
  const [displayedLength, setDisplayedLength] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // If there's content to type and no interval running, start typing
    if (content.length > displayedLength && !intervalRef.current) {
      intervalRef.current = setInterval(() => {
        setDisplayedLength(prev => {
          // Type 2-3 chars per tick for smooth but fast appearance
          const next = Math.min(prev + 3, content.length);
          if (next >= content.length) {
            // Caught up — pause the interval until more content arrives
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
          }
          return next;
        });
      }, 15); // ~66 chars/sec — fast enough to feel real-time
    }

    return () => {
      // Don't clear on every render — only on unmount
    };
  }, [content.length]); // Re-trigger when server sends more content

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, []);

  const displayedText = content.slice(0, displayedLength);
  const isTyping = displayedLength < content.length;

  return (
    <div className="flex gap-3 mb-6 animate-slide-up">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center mt-0.5 bg-gradient-to-br from-[#0A84FF] to-[#5E5CE6]">
        <HiSparkles className="w-4 h-4 text-white" />
      </div>

      {/* Message content */}
      <div className="flex-1 min-w-0">
        <div className="rounded-2xl px-4 py-3 max-w-[85%] inline-block bg-apple-surface glass-border text-white/90 rounded-tl-md">
          <div className="markdown-content text-sm">
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
              }}
            >
              {displayedText}
            </ReactMarkdown>
            {/* Blinking cursor while typing */}
            {isTyping && (
              <span className="inline-block w-0.5 h-4 bg-apple-accent animate-pulse ml-0.5 align-text-bottom" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StreamingBubble;

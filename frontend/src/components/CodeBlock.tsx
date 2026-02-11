import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { HiOutlineClipboard, HiOutlineCheck } from 'react-icons/hi2';

interface CodeBlockProps {
  language: string;
  value: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, value }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-3 rounded-xl overflow-hidden bg-[#1a1a2e] border border-apple-border/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-apple-elevated/50 border-b border-apple-border/30">
        <span className="text-[11px] font-medium text-apple-tertiary uppercase tracking-wider">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[11px] text-apple-tertiary hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <HiOutlineCheck className="w-3.5 h-3.5 text-apple-green" />
              <span className="text-apple-green">Copied</span>
            </>
          ) : (
            <>
              <HiOutlineClipboard className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code */}
      <SyntaxHighlighter
        language={language || 'text'}
        style={oneDark}
        customStyle={{
          margin: 0,
          padding: '1em',
          background: 'transparent',
          fontSize: '13px',
          lineHeight: '1.5',
        }}
        showLineNumbers={value.split('\n').length > 3}
        lineNumberStyle={{ color: '#636366', fontSize: '11px' }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
};

export default CodeBlock;

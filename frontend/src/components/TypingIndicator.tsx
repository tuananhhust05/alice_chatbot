import React from 'react';
import { HiSparkles } from 'react-icons/hi2';

const TypingIndicator: React.FC = () => {
  return (
    <div className="flex gap-3 mb-6 animate-fade-in">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-[#0A84FF] to-[#5E5CE6] flex items-center justify-center">
        <HiSparkles className="w-4 h-4 text-white" />
      </div>

      {/* Typing dots */}
      <div className="bg-apple-surface glass-border rounded-2xl rounded-tl-md px-5 py-4">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-apple-secondary typing-dot" />
          <div className="w-2 h-2 rounded-full bg-apple-secondary typing-dot" />
          <div className="w-2 h-2 rounded-full bg-apple-secondary typing-dot" />
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;

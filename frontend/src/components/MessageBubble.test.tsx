import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MessageBubble from './MessageBubble';
import { Message } from '../types';

// Helper to create message
const createMessage = (overrides: Partial<Message> = {}): Message => ({
  role: 'user',
  content: 'Hello, world!',
  timestamp: '2024-01-01T00:00:00Z',
  ...overrides,
});

describe('MessageBubble', () => {
  describe('User messages', () => {
    it('should render user message content', () => {
      const message = createMessage({ role: 'user', content: 'Hello, AI!' });
      render(<MessageBubble message={message} />);

      expect(screen.getByTestId('user-message-content')).toHaveTextContent('Hello, AI!');
    });

    it('should render user avatar', () => {
      const message = createMessage({ role: 'user' });
      render(<MessageBubble message={message} />);

      expect(screen.getByTestId('user-avatar')).toBeInTheDocument();
    });

    it('should have correct testid for user message', () => {
      const message = createMessage({ role: 'user' });
      render(<MessageBubble message={message} />);

      expect(screen.getByTestId('message-bubble-user')).toBeInTheDocument();
    });
  });

  describe('Assistant messages', () => {
    it('should render assistant message content', () => {
      const message = createMessage({ role: 'assistant', content: 'Hello, human!' });
      render(<MessageBubble message={message} />);

      expect(screen.getByTestId('assistant-message-content')).toBeInTheDocument();
    });

    it('should render assistant avatar', () => {
      const message = createMessage({ role: 'assistant' });
      render(<MessageBubble message={message} />);

      expect(screen.getByTestId('assistant-avatar')).toBeInTheDocument();
    });

    it('should render markdown content', () => {
      const message = createMessage({
        role: 'assistant',
        content: '**Bold text** and *italic*',
      });
      render(<MessageBubble message={message} />);

      // Markdown should be rendered
      expect(screen.getByText('Bold text')).toBeInTheDocument();
    });
  });

  describe('File attachments', () => {
    it('should show file attachment badge when file is attached', () => {
      const message = createMessage({
        role: 'user',
        content: '[Attached: report.pdf]\n\nPlease analyze this',
      });
      render(<MessageBubble message={message} />);

      expect(screen.getByTestId('file-attachment-badge')).toBeInTheDocument();
      expect(screen.getByTestId('attached-file-name')).toHaveTextContent('report.pdf');
    });

    it('should show only the display content, not the attachment marker', () => {
      const message = createMessage({
        role: 'user',
        content: '[Attached: data.csv]\n\nAnalyze the data',
      });
      render(<MessageBubble message={message} />);

      expect(screen.getByTestId('user-message-content')).toHaveTextContent('Analyze the data');
      expect(screen.getByTestId('user-message-content')).not.toHaveTextContent('[Attached:');
    });

    it('should show default text when only file is attached', () => {
      const message = createMessage({
        role: 'user',
        content: '[Attached: file.xlsx]\n\nPlease analyze this file.',
      });
      render(<MessageBubble message={message} />);

      expect(screen.getByTestId('user-message-content')).toHaveTextContent('Please analyze this file.');
    });

    it('should not show file badge when no attachment', () => {
      const message = createMessage({
        role: 'user',
        content: 'Regular message without file',
      });
      render(<MessageBubble message={message} />);

      expect(screen.queryByTestId('file-attachment-badge')).not.toBeInTheDocument();
    });

    it('should not show file badge for assistant messages', () => {
      const message = createMessage({
        role: 'assistant',
        content: '[Attached: file.pdf]\n\nSome content',
      });
      render(<MessageBubble message={message} />);

      // Assistant messages don't show file badges (they show full content)
      expect(screen.queryByTestId('file-attachment-badge')).not.toBeInTheDocument();
    });
  });

  describe('Code blocks', () => {
    it('should render code blocks', () => {
      const message = createMessage({
        role: 'assistant',
        content: '```javascript\nconst x = 1;\n```',
      });
      const { container } = render(<MessageBubble message={message} />);

      // Check that code block is rendered with syntax highlighting
      // The syntax highlighter splits text into multiple spans, so we check for the code element
      const codeElement = container.querySelector('code.language-javascript');
      expect(codeElement).toBeInTheDocument();
    });

    it('should render inline code', () => {
      const message = createMessage({
        role: 'assistant',
        content: 'Use `npm install` to install',
      });
      render(<MessageBubble message={message} />);

      expect(screen.getByText('npm install')).toBeInTheDocument();
    });
  });

  describe('Empty content', () => {
    it('should show default text for empty user message with file', () => {
      const message = createMessage({
        role: 'user',
        content: '[Attached: data.xlsx]\n\n',
      });
      render(<MessageBubble message={message} />);

      expect(screen.getByTestId('user-message-content')).toHaveTextContent('Please analyze this file.');
    });
  });
});

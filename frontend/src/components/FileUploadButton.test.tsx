import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileUploadButton from './FileUploadButton';

describe('FileUploadButton', () => {
  describe('Rendering', () => {
    it('should render upload button', () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={false} />);

      expect(screen.getByTestId('file-upload-button')).toBeInTheDocument();
    });

    it('should have hidden file input', () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={false} />);

      const input = screen.getByTestId('file-input');
      expect(input).toBeInTheDocument();
      expect(input).toHaveClass('hidden');
    });

    it('should accept correct file types', () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={false} />);

      const input = screen.getByTestId('file-input');
      expect(input).toHaveAttribute('accept', '.pdf,.txt,.csv,.docx,.xlsx');
    });
  });

  describe('Disabled state', () => {
    it('should be disabled when disabled prop is true', () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={true} />);

      expect(screen.getByTestId('file-upload-button')).toBeDisabled();
    });

    it('should not be disabled when disabled prop is false', () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={false} />);

      expect(screen.getByTestId('file-upload-button')).not.toBeDisabled();
    });
  });

  describe('File selection', () => {
    it('should call onFileSelect when file is selected', async () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={false} />);

      const input = screen.getByTestId('file-input') as HTMLInputElement;
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      // Simulate file selection
      fireEvent.change(input, { target: { files: [file] } });

      expect(mockOnFileSelect).toHaveBeenCalledTimes(1);
      expect(mockOnFileSelect).toHaveBeenCalledWith(file);
    });

    it('should not call onFileSelect when no file is selected', () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={false} />);

      const input = screen.getByTestId('file-input') as HTMLInputElement;

      // Simulate empty file selection
      fireEvent.change(input, { target: { files: [] } });

      expect(mockOnFileSelect).not.toHaveBeenCalled();
    });

    it('should reset input after file selection', () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={false} />);

      const input = screen.getByTestId('file-input') as HTMLInputElement;
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      // First selection
      fireEvent.change(input, { target: { files: [file] } });

      // Input should be reset (value should be empty)
      expect(input.value).toBe('');
    });
  });

  describe('Button click', () => {
    it('should trigger file input click when button is clicked', async () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={false} />);

      const input = screen.getByTestId('file-input') as HTMLInputElement;
      const clickSpy = vi.spyOn(input, 'click');

      const user = userEvent.setup();
      await user.click(screen.getByTestId('file-upload-button'));

      expect(clickSpy).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have title attribute', () => {
      const mockOnFileSelect = vi.fn();
      render(<FileUploadButton onFileSelect={mockOnFileSelect} disabled={false} />);

      const button = screen.getByTestId('file-upload-button');
      expect(button).toHaveAttribute('title');
      expect(button.getAttribute('title')).toContain('Upload file');
    });
  });
});

import { describe, it, expect, vi } from 'vitest';
import { extractFileContent } from './files';
import api from './client';

// Mock the api client
vi.mock('./client', () => ({
  default: {
    post: vi.fn(),
  },
}));

describe('Files API', () => {
  describe('extractFileContent', () => {
    it('should extract content from file', async () => {
      const mockResponse = {
        text: 'Extracted text content',
        original_name: 'test.pdf',
        file_type: 'pdf',
        file_size: 1024,
        text_length: 22,
        text_truncated: false,
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const mockFile = new File(['test content'], 'test.pdf', {
        type: 'application/pdf',
      });

      const result = await extractFileContent(mockFile);

      expect(result).toHaveProperty('text');
      expect(result).toHaveProperty('original_name');
      expect(result).toHaveProperty('file_type');
      expect(result).toHaveProperty('file_size');
      expect(result).toHaveProperty('text_length');
      expect(result).toHaveProperty('text_truncated');
    });

    it('should return expected structure', async () => {
      const mockResponse = {
        text: 'Extracted text content',
        original_name: 'test.pdf',
        file_type: 'pdf',
        file_size: 1024,
        text_length: 22,
        text_truncated: false,
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const mockFile = new File(['content'], 'document.pdf', {
        type: 'application/pdf',
      });

      const result = await extractFileContent(mockFile);

      expect(result.original_name).toBe('test.pdf');
      expect(result.file_type).toBe('pdf');
      expect(result.text_truncated).toBe(false);
    });
  });
});

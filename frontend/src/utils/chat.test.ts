import { describe, it, expect } from 'vitest';
import {
  parseAttachedFile,
  buildActualMessage,
  buildDisplayContent,
  formatFileSize,
  isValidFileType,
  getFileExtension,
  truncateText,
  isValidMessage,
  hasFileAttachment,
  SUPPORTED_FILE_TYPES,
} from './chat';

describe('parseAttachedFile', () => {
  it('should parse file name from attached message', () => {
    const content = '[Attached: report.pdf]\n\nPlease analyze this';
    const result = parseAttachedFile(content);
    
    expect(result.fileName).toBe('report.pdf');
    expect(result.displayContent).toBe('Please analyze this');
  });

  it('should handle message without attachment', () => {
    const content = 'Hello, how are you?';
    const result = parseAttachedFile(content);
    
    expect(result.fileName).toBeNull();
    expect(result.displayContent).toBe('Hello, how are you?');
  });

  it('should handle empty message with attachment', () => {
    const content = '[Attached: data.csv]\n\nPlease analyze this file.';
    const result = parseAttachedFile(content);
    
    expect(result.fileName).toBe('data.csv');
    expect(result.displayContent).toBe('Please analyze this file.');
  });

  it('should handle file names with spaces', () => {
    const content = '[Attached: my report 2024.xlsx]\n\nSummarize this';
    const result = parseAttachedFile(content);
    
    expect(result.fileName).toBe('my report 2024.xlsx');
    expect(result.displayContent).toBe('Summarize this');
  });

  it('should not parse if format is wrong', () => {
    const content = 'Attached: report.pdf\n\nSome text';
    const result = parseAttachedFile(content);
    
    expect(result.fileName).toBeNull();
    expect(result.displayContent).toBe(content);
  });
});

describe('buildActualMessage', () => {
  it('should build message with file content', () => {
    const result = buildActualMessage('Analyze this', {
      name: 'data.csv',
      text: 'col1,col2\n1,2',
    });
    
    expect(result).toBe('Analyze this\n\nFile content:\n[File: data.csv]\ncol1,col2\n1,2');
  });

  it('should use default text when user text is empty', () => {
    const result = buildActualMessage('', {
      name: 'data.csv',
      text: 'col1,col2',
    });
    
    expect(result).toContain('Please analyze this file.');
    expect(result).toContain('[File: data.csv]');
  });

  it('should return user text only when no file', () => {
    const result = buildActualMessage('Hello world', null);
    
    expect(result).toBe('Hello world');
  });

  it('should return empty string when no text and no file', () => {
    const result = buildActualMessage('', null);
    
    expect(result).toBe('');
  });
});

describe('buildDisplayContent', () => {
  it('should build display content with file marker', () => {
    const result = buildDisplayContent('Check this file', { name: 'report.pdf' });
    
    expect(result).toBe('[Attached: report.pdf]\n\nCheck this file');
  });

  it('should use default text when user text is empty', () => {
    const result = buildDisplayContent('', { name: 'data.xlsx' });
    
    expect(result).toBe('[Attached: data.xlsx]\n\nPlease analyze this file.');
  });

  it('should return user text only when no file', () => {
    const result = buildDisplayContent('Hello', null);
    
    expect(result).toBe('Hello');
  });
});

describe('formatFileSize', () => {
  it('should format bytes', () => {
    expect(formatFileSize(500)).toBe('500 B');
    expect(formatFileSize(0)).toBe('0 B');
  });

  it('should format kilobytes', () => {
    expect(formatFileSize(1024)).toBe('1.0 KB');
    expect(formatFileSize(1536)).toBe('1.5 KB');
    expect(formatFileSize(10240)).toBe('10.0 KB');
  });

  it('should format megabytes', () => {
    expect(formatFileSize(1024 * 1024)).toBe('1.0 MB');
    expect(formatFileSize(1.5 * 1024 * 1024)).toBe('1.5 MB');
    expect(formatFileSize(10 * 1024 * 1024)).toBe('10.0 MB');
  });
});

describe('isValidFileType', () => {
  it('should accept supported file types', () => {
    expect(isValidFileType('document.pdf')).toBe(true);
    expect(isValidFileType('notes.txt')).toBe(true);
    expect(isValidFileType('data.csv')).toBe(true);
    expect(isValidFileType('report.docx')).toBe(true);
    expect(isValidFileType('spreadsheet.xlsx')).toBe(true);
  });

  it('should reject unsupported file types', () => {
    expect(isValidFileType('image.png')).toBe(false);
    expect(isValidFileType('video.mp4')).toBe(false);
    expect(isValidFileType('script.js')).toBe(false);
    expect(isValidFileType('archive.zip')).toBe(false);
  });

  it('should handle files without extension', () => {
    expect(isValidFileType('filename')).toBe(false);
  });

  it('should be case insensitive', () => {
    expect(isValidFileType('DOCUMENT.PDF')).toBe(true);
    expect(isValidFileType('Data.CSV')).toBe(true);
  });
});

describe('getFileExtension', () => {
  it('should extract extension', () => {
    expect(getFileExtension('file.pdf')).toBe('pdf');
    expect(getFileExtension('file.txt')).toBe('txt');
  });

  it('should handle multiple dots', () => {
    expect(getFileExtension('file.backup.pdf')).toBe('pdf');
  });

  it('should return lowercase', () => {
    expect(getFileExtension('FILE.PDF')).toBe('pdf');
  });

  it('should handle no extension', () => {
    expect(getFileExtension('filename')).toBe('');
  });
});

describe('truncateText', () => {
  it('should not truncate short text', () => {
    expect(truncateText('Hello', 10)).toBe('Hello');
  });

  it('should truncate long text with ellipsis', () => {
    expect(truncateText('Hello, world!', 10)).toBe('Hello, ...');
  });

  it('should handle exact length', () => {
    expect(truncateText('Hello', 5)).toBe('Hello');
  });

  it('should handle very short max length', () => {
    expect(truncateText('Hello', 4)).toBe('H...');
  });
});

describe('isValidMessage', () => {
  it('should accept non-empty messages', () => {
    expect(isValidMessage('Hello')).toBe(true);
    expect(isValidMessage('  Hello  ')).toBe(true);
  });

  it('should reject empty messages', () => {
    expect(isValidMessage('')).toBe(false);
    expect(isValidMessage('   ')).toBe(false);
    expect(isValidMessage('\n\t')).toBe(false);
  });
});

describe('hasFileAttachment', () => {
  it('should detect file attachment marker', () => {
    expect(hasFileAttachment('[Attached: file.pdf]\n\nHello')).toBe(true);
    expect(hasFileAttachment('[Attached: data.csv]\n\n')).toBe(true);
  });

  it('should not detect without marker', () => {
    expect(hasFileAttachment('Hello, world!')).toBe(false);
    expect(hasFileAttachment('Attached: file.pdf')).toBe(false);
  });
});

describe('SUPPORTED_FILE_TYPES', () => {
  it('should include expected types', () => {
    expect(SUPPORTED_FILE_TYPES).toContain('pdf');
    expect(SUPPORTED_FILE_TYPES).toContain('txt');
    expect(SUPPORTED_FILE_TYPES).toContain('csv');
    expect(SUPPORTED_FILE_TYPES).toContain('docx');
    expect(SUPPORTED_FILE_TYPES).toContain('xlsx');
  });
});

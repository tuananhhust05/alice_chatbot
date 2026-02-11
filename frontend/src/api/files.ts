import api from './client';
import { FileExtractResponse } from '../types';

/**
 * Extract text content from uploaded file.
 * Backend reads file, extracts text, returns immediately (no Kafka).
 */
export const extractFileContent = async (file: File): Promise<FileExtractResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await api.post('/api/files/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

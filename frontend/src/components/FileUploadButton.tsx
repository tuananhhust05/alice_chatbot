import React, { useRef } from 'react';
import { HiOutlinePaperClip } from 'react-icons/hi2';

interface FileUploadButtonProps {
  onFileSelect: (file: File) => void;
  disabled: boolean;
}

// Supported file types: PDF, TXT, CSV, DOCX, XLSX
const ACCEPTED_TYPES = '.pdf,.txt,.csv,.docx,.xlsx';

const FileUploadButton: React.FC<FileUploadButtonProps> = ({ onFileSelect, disabled }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
      // Reset input so same file can be uploaded again
      e.target.value = '';
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        onChange={handleChange}
        className="hidden"
        data-testid="file-input"
      />
      <button
        onClick={handleClick}
        disabled={disabled}
        className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-full text-apple-secondary hover:text-white hover:bg-apple-hover/50 transition-all mb-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
        title="Upload file (PDF, TXT, CSV, DOCX, XLSX)"
        data-testid="file-upload-button"
      >
        <HiOutlinePaperClip className="w-[18px] h-[18px]" />
      </button>
    </>
  );
};

export default FileUploadButton;

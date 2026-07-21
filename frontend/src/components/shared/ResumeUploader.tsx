/**
 * ResumeUploader Component
 *
 * Drag-and-drop file upload dropzone supporting PDF resume files.
 * Provides visual feedback during drag over and upload processing.
 */

import { useState, useRef } from "react";
import { UploadCloud, FileText, AlertCircle } from "lucide-react";
import { Button, Spinner } from "../ui";

interface ResumeUploaderProps {
  onUpload: (file: File) => void;
  isLoading?: boolean;
}

function ResumeUploader({ onUpload, isLoading = false }: ResumeUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setErrorMsg(null);
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMsg("Please upload a PDF file (.pdf)");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg("File size exceeds 10 MB limit.");
      return;
    }

    onUpload(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  return (
    <div className="w-full">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-[20px] p-12 text-center transition-all cursor-pointer ${
          isDragOver
            ? "border-primary bg-primary/5 scale-[0.99]"
            : "border-border hover:border-primary/50 bg-surface/40 hover:bg-surface-elevated/40 shadow-sm hover:shadow-md"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="h-14 w-14 rounded-full bg-primary-muted text-primary flex items-center justify-center">
            {isLoading ? (
              <Spinner size="md" />
            ) : (
              <UploadCloud size={28} />
            )}
          </div>
          <div className="space-y-1">
            <h4 className="text-lg font-semibold text-text">
              {isLoading ? "Uploading resume..." : "Click or drag & drop to upload"}
            </h4>
            <p className="text-xs text-text-secondary mt-1">
              Supports PDF documents up to 10 MB
            </p>
          </div>

          {!isLoading && (
            <Button type="button" variant="secondary" size="sm" icon={<FileText size={14} />}>
              Select PDF File
            </Button>
          )}
        </div>
      </div>

      {errorMsg && (
        <div className="mt-3 flex items-center gap-2 text-xs text-error">
          <AlertCircle size={14} />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
}

export default ResumeUploader;

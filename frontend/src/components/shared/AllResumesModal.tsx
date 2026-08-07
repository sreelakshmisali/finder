/**
 * AllResumesModal Component
 *
 * Displays all uploaded resumes for the user in a future-proof modal.
 * Shows filename, upload date, active badge, parsed role/summary, and extracted skills count.
 * Allows switching the active resume, uploading new resumes, and deleting resumes.
 */

import { useState } from "react";
import { Modal, Button, Badge } from "../ui";
import ResumeUploader from "./ResumeUploader";
import type { Resume, ParsedResumeData } from "../../types/resume";
import { CheckCircle2, FileText, Trash2, Plus, Calendar, Layers, Briefcase } from "lucide-react";

interface AllResumesModalProps {
  isOpen: boolean;
  onClose: () => void;
  resumes: Resume[];
  activeResumeId?: string;
  onSetActive: (resumeId: string) => void;
  onDelete: (resumeId: string) => void;
  onUpload: (file: File) => void;
  isActivating?: boolean;
  isDeleting?: boolean;
  isUploading?: boolean;
}

export default function AllResumesModal({
  isOpen,
  onClose,
  resumes,
  activeResumeId,
  onSetActive,
  onDelete,
  onUpload,
  isActivating,
  isDeleting,
  isUploading,
}: AllResumesModalProps) {
  const [showUploader, setShowUploader] = useState(false);

  const handleUploadSuccess = (file: File) => {
    onUpload(file);
    setShowUploader(false);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="My Resumes"
      size="lg"
    >
      <div className="space-y-6">
        <p className="text-xs text-text-secondary">
          Manage your uploaded resumes. Only one resume can be active at a time for search and AI fit recommendations.
        </p>

        {/* Resumes List */}
        <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
          {resumes.length === 0 ? (
            <div className="p-8 border border-dashed border-border rounded-xl text-center space-y-2">
              <FileText size={32} className="mx-auto text-text-muted opacity-50" />
              <p className="text-sm font-semibold text-text">No resumes uploaded yet</p>
              <p className="text-xs text-text-secondary">Upload a PDF resume to get started.</p>
            </div>
          ) : (
            resumes.map((resume) => {
              const isActive = resume.id === activeResumeId || resume.is_active;
              const parsed = resume.parsed_data as ParsedResumeData | null;
              const skillsCount = parsed?.skills && Array.isArray(parsed.skills) ? parsed.skills.length : 0;
              const primaryRole = parsed?.full_name || (parsed?.experience?.[0] as any)?.title || null;
              const uploadDate = new Date(resume.uploaded_at).toLocaleDateString(undefined, {
                year: "numeric",
                month: "short",
                day: "numeric",
              });

              return (
                <div
                  key={resume.id}
                  className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                    isActive
                      ? "bg-primary/5 border-primary/40 ring-1 ring-primary/30"
                      : "bg-surface-elevated/40 border-border hover:border-border/80"
                  }`}
                >
                  {/* Info Column */}
                  <div className="space-y-1.5 min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <FileText size={18} className={isActive ? "text-primary shrink-0" : "text-text-muted shrink-0"} />
                      <span className="font-bold text-sm text-text truncate max-w-xs">{resume.filename}</span>
                      {isActive && (
                        <Badge variant="success" className="text-[10px] font-bold gap-1 flex items-center">
                          <CheckCircle2 size={11} /> Active
                        </Badge>
                      )}
                    </div>

                    {/* Metadata Row */}
                    <div className="flex flex-wrap items-center gap-3 text-xs text-text-secondary">
                      <span className="flex items-center gap-1">
                        <Calendar size={12} className="text-text-muted" /> {uploadDate}
                      </span>

                      {primaryRole && (
                        <span className="flex items-center gap-1 font-medium text-text">
                          <Briefcase size={12} className="text-accent" /> {primaryRole}
                        </span>
                      )}

                      {skillsCount > 0 && (
                        <span className="flex items-center gap-1 font-medium text-text">
                          <Layers size={12} className="text-success" /> {skillsCount} skills extracted
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions Row */}
                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    {!isActive && (
                      <Button
                        variant="secondary"
                        size="sm"
                        isLoading={isActivating}
                        onClick={() => onSetActive(resume.id)}
                        className="text-xs"
                      >
                        Set Active
                      </Button>
                    )}

                    <Button
                      variant="danger"
                      size="sm"
                      isLoading={isDeleting}
                      onClick={() => onDelete(resume.id)}
                      icon={<Trash2 size={13} />}
                      title="Delete Resume"
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Upload New Section */}
        {showUploader ? (
          <div className="p-4 bg-surface-elevated/40 border border-border rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-text">Upload New Resume</h4>
              <button
                type="button"
                onClick={() => setShowUploader(false)}
                className="text-xs text-text-muted hover:text-text cursor-pointer font-medium"
              >
                Cancel
              </button>
            </div>
            <ResumeUploader onUpload={handleUploadSuccess} isLoading={isUploading} />
          </div>
        ) : (
          <div className="flex items-center justify-between border-t border-border pt-4">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowUploader(true)}
              icon={<Plus size={14} />}
            >
              Upload New Resume
            </Button>

            <Button variant="primary" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}

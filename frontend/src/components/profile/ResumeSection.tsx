/**
 * ResumeSection Component
 *
 * Section 1 of Profile Setup Page:
 * Handles PDF upload, active resume selection, and displays extracted candidate capabilities
 * (Name, Skills, Experience, and Roles). Reuses ResumeUploader, ResumeCard, and ParsedResumeView.
 */

import { useState } from "react";
import ResumeUploader from "../shared/ResumeUploader";
import ResumeCard from "../shared/ResumeCard";
import ParsedResumeView from "../shared/ParsedResumeView";
import EmptyState from "../shared/EmptyState";
import { Card, CardHeader, CardTitle, Modal, Spinner, Button, Badge } from "../ui";
import {
  useResumes,
  useUploadResume,
  useSetActiveResume,
  useParseResume,
  useDeleteResume,
} from "../../hooks/useResume";
import type { Resume } from "../../types/resume";
import type { ResumeSummary } from "../../types/profile";
import {
  FileText,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Trash2,
  User,
  Briefcase,
  Layers,
} from "lucide-react";

interface ResumeSectionProps {
  summary?: ResumeSummary | null;
}

export default function ResumeSection({ summary }: ResumeSectionProps) {
  const [selectedResumeForView, setSelectedResumeForView] = useState<Resume | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [resumeToDelete, setResumeToDelete] = useState<Resume | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data: resumesData, isLoading, isError } = useResumes();
  const uploadMutation = useUploadResume();
  const setActiveMutation = useSetActiveResume();
  const parseMutation = useParseResume();
  const deleteMutation = useDeleteResume();

  const handleUpload = (file: File) => {
    uploadMutation.mutate(file);
  };

  const handleSetActive = (resumeId: string) => {
    setActiveMutation.mutate(resumeId);
  };

  const handleParseOrCreateView = (resumeId: string) => {
    const target = resumes.find((r) => r.id === resumeId);
    if (!target) return;

    if (target.parsed_data) {
      setSelectedResumeForView(target);
      setIsModalOpen(true);
    } else {
      parseMutation.mutate(resumeId, {
        onSuccess: (updatedResume) => {
          setSelectedResumeForView(updatedResume);
          setIsModalOpen(true);
        },
      });
    }
  };

  const handleConfirmDelete = () => {
    if (!resumeToDelete) return;
    setDeleteError(null);

    deleteMutation.mutate(resumeToDelete.id, {
      onSuccess: () => {
        setResumeToDelete(null);
        setDeleteError(null);
      },
      onError: (error: any) => {
        const errorMsg =
          error?.response?.data?.detail ||
          error?.message ||
          "Failed to delete resume.";
        setDeleteError(errorMsg);
      },
    });
  };

  const resumes = resumesData?.resumes || [];

  return (
    <div id="resume-section" className="space-y-6 scroll-mt-6">
      {/* Section Header */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-xl font-black text-text tracking-tight">
              1. Resume Capabilities
            </h3>
            <Badge variant="error" className="text-xs px-2.5 py-0.5 font-bold uppercase">
              Required
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Upload your PDF resume to extract skills, experience history, and target roles.
          </p>
        </div>
      </div>

      {/* Extracted Resume Summary Highlight Card */}
      {summary && summary.has_resume && (
        <Card className="border-primary/40 bg-surface-elevated/40">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-primary">
                <CheckCircle2 size={18} />
                <span>Extracted Resume Insights</span>
              </div>
              <span className="text-xs text-text-muted">{summary.filename}</span>
            </div>

            {/* Extracted Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-border/50">
              {/* Name & Contact */}
              <div className="space-y-1">
                <span className="text-xs uppercase font-bold text-text-muted flex items-center gap-1.5">
                  <User size={14} className="text-primary" /> Candidate Contact
                </span>
                <p className="text-sm font-semibold text-text">
                  {summary.full_name || "Name not extracted"}
                </p>
                <p className="text-xs text-text-secondary">
                  {[summary.email, summary.phone].filter(Boolean).join(" • ") || "Contact info pending"}
                </p>
              </div>

              {/* Extracted Target Roles */}
              <div className="space-y-1">
                <span className="text-xs uppercase font-bold text-text-muted flex items-center gap-1.5">
                  <Briefcase size={14} className="text-accent" /> Extracted Roles
                </span>
                {summary.roles && summary.roles.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 pt-0.5">
                    {summary.roles.slice(0, 4).map((role, idx) => (
                      <Badge key={idx} variant="primary" className="text-[11px] px-2 py-0.5">
                        {role}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-secondary">No roles extracted</p>
                )}
              </div>
            </div>

            {/* Extracted Skills Matrix */}
            <div className="space-y-1.5 pt-2 border-t border-border/50">
              <span className="text-xs uppercase font-bold text-text-muted flex items-center gap-1.5">
                <Layers size={14} className="text-success" /> Extracted Skills ({summary.skills.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {summary.skills.slice(0, 12).map((skill, idx) => (
                  <Badge key={idx} variant="default" className="text-xs px-2.5 py-1 bg-surface border border-border">
                    {skill}
                  </Badge>
                ))}
                {summary.skills.length > 12 && (
                  <span className="text-xs text-text-muted font-medium self-center pl-1">
                    +{summary.skills.length - 12} more
                  </span>
                )}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Main Upload Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        {/* Left Column: PDF Dropzone */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText size={18} className="text-primary" />
                Upload PDF Resume
              </CardTitle>
            </CardHeader>

            <ResumeUploader
              onUpload={handleUpload}
              isLoading={uploadMutation.isPending}
            />
          </Card>
        </div>

        {/* Right Column: Uploaded Resumes History */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles size={18} className="text-accent" />
                Uploaded Resumes ({resumes.length})
              </CardTitle>
            </CardHeader>

            {isLoading && (
              <div className="flex justify-center py-12">
                <Spinner size="md" />
              </div>
            )}

            {isError && (
              <div className="p-4 text-xs text-error">
                Failed to load resumes. Check backend connection.
              </div>
            )}

            {!isLoading && !isError && resumes.length === 0 && (
              <EmptyState
                icon={<FileText size={48} />}
                title="No resumes uploaded yet"
                description="Upload your PDF resume on the left to extract skills, experience, and roles."
              />
            )}

            {!isLoading && !isError && resumes.length > 0 && (
              <div className="space-y-4">
                {resumes.map((resume) => (
                  <ResumeCard
                    key={resume.id}
                    resume={resume}
                    onSetActive={handleSetActive}
                    onParse={handleParseOrCreateView}
                    onDelete={(r) => {
                      setDeleteError(null);
                      setResumeToDelete(r);
                    }}
                    isSettingActive={setActiveMutation.isPending}
                    isDeleting={deleteMutation.isPending && deleteMutation.variables === resume.id}
                  />
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Parsed Resume Details Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Parsed Details: ${selectedResumeForView?.filename || ""}`}
        size="lg"
      >
        {parseMutation.isPending ? (
          <div className="flex flex-col items-center justify-center py-12 space-y-3">
            <Spinner size="lg" />
            <p className="text-sm text-text-secondary">
              Analyzing PDF text with AI provider...
            </p>
          </div>
        ) : (
          <ParsedResumeView data={selectedResumeForView?.parsed_data} />
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!resumeToDelete}
        onClose={() => {
          setResumeToDelete(null);
          setDeleteError(null);
        }}
        title="Permanent Resume Deletion"
        size="md"
      >
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 rounded-lg bg-error/10 border border-error/20 text-error">
            <AlertTriangle size={24} className="shrink-0 mt-0.5" />
            <div className="text-sm space-y-1">
              <p className="font-semibold">
                Are you sure you want to delete "{resumeToDelete?.filename}"?
              </p>
              <p className="text-xs opacity-90">
                This action is permanent and cannot be undone. Physical PDF storage and database records will be deleted.
              </p>
            </div>
          </div>

          {deleteError && (
            <div className="p-3 text-xs rounded bg-error/20 text-error font-medium border border-error/30">
              {deleteError}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setResumeToDelete(null);
                setDeleteError(null);
              }}
            >
              Cancel
            </Button>

            <Button
              variant="danger"
              size="sm"
              isLoading={deleteMutation.isPending}
              onClick={handleConfirmDelete}
              icon={<Trash2 size={14} />}
            >
              Delete Resume
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

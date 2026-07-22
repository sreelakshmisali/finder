/**
 * Resume Page Component
 *
 * Full resume upload, active resume selection, and AI parsing viewer.
 */

import { useState } from "react";
import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import ResumeUploader from "../components/shared/ResumeUploader";
import ResumeCard from "../components/shared/ResumeCard";
import ParsedResumeView from "../components/shared/ParsedResumeView";
import EmptyState from "../components/shared/EmptyState";
import { Card, CardHeader, CardTitle, Modal, Spinner, Button } from "../components/ui";
import {
  useResumes,
  useUploadResume,
  useSetActiveResume,
  useParseResume,
  useDeleteResume,
} from "../hooks/useResume";
import type { Resume } from "../types/resume";
import { FileText, Sparkles, CheckCircle2, AlertTriangle, Trash2 } from "lucide-react";

function ResumePage() {
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
  const activeResume = resumes.find((r) => r.is_active);

  return (
    <>
      <Header
        title="Resume Management"
        subtitle="Upload and manage PDF resumes for AI job matching"
      />

      <PageWrapper>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 max-w-7xl mx-auto w-full">
          {/* Upload Dropzone Column (1 col) */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText size={18} className="text-primary" />
                  Upload New Resume
                </CardTitle>
              </CardHeader>

              <ResumeUploader
                onUpload={handleUpload}
                isLoading={uploadMutation.isPending}
              />
            </Card>

            {/* Active Resume Quick Highlight */}
            {activeResume && (
              <Card className="border-primary/40 bg-primary-muted/10">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-primary-muted text-primary flex items-center justify-center shrink-0">
                    <CheckCircle2 size={20} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <span className="text-[10px] uppercase font-bold text-primary tracking-wider">
                      Currently Active Resume
                    </span>
                    <h4 className="text-sm font-semibold text-text truncate">
                      {activeResume.filename}
                    </h4>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* Resume History List Column (2 cols) */}
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
                  description="Upload your PDF resume on the left to start extracting skills and matching jobs."
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
                  This action is permanent and cannot be undone. The PDF file will be removed completely from disk storage and database records.
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
      </PageWrapper>
    </>
  );
}

export default ResumePage;


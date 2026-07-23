/**
 * Resume Page Component
 *
 * Full resume upload, active resume selection, AI parsing viewer,
 * and AI Resume Improvement Quality Audit & Job-Specific Tailoring Assistant.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import ResumeUploader from "../components/shared/ResumeUploader";
import ResumeCard from "../components/shared/ResumeCard";
import ParsedResumeView from "../components/shared/ParsedResumeView";
import EmptyState from "../components/shared/EmptyState";
import { Card, CardHeader, CardTitle, Modal, Spinner, Button, Badge, Input } from "../components/ui";
import {
  useResumes,
  useUploadResume,
  useSetActiveResume,
  useParseResume,
  useDeleteResume,
  useResumeQualityAnalysis,
  useJobSpecificSuggestions,
} from "../hooks/useResume";
import type { Resume, ResumeQualityAnalysis, JobSpecificSuggestions } from "../types/resume";
import {
  FileText,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Zap,
  Target,
  Wand2,
  Check,
  XCircle,
} from "lucide-react";

function ResumePage() {
  const navigate = useNavigate();
  const [selectedResumeForView, setSelectedResumeForView] = useState<Resume | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [resumeToDelete, setResumeToDelete] = useState<Resume | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // AI Improvement State
  const [qualityAudit, setQualityAudit] = useState<ResumeQualityAnalysis | null>(null);
  const [jobTitleInput, setJobTitleInput] = useState("");
  const [jobDescInput, setJobDescInput] = useState("");
  const [jobSuggestions, setJobSuggestions] = useState<JobSpecificSuggestions | null>(null);

  const { data: resumesData, isLoading, isError } = useResumes();
  const uploadMutation = useUploadResume();
  const setActiveMutation = useSetActiveResume();
  const parseMutation = useParseResume();
  const deleteMutation = useDeleteResume();

  const qualityAnalysisMutation = useResumeQualityAnalysis();
  const jobSuggestionsMutation = useJobSpecificSuggestions();

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

  const handleRunQualityAudit = (resumeId: string) => {
    qualityAnalysisMutation.mutate(resumeId, {
      onSuccess: (data) => setQualityAudit(data),
    });
  };

  const handleRunJobSuggestions = (resumeId: string) => {
    jobSuggestionsMutation.mutate(
      {
        resumeId,
        payload: {
          job_title: jobTitleInput.trim() || undefined,
          job_description: jobDescInput.trim() || undefined,
        },
      },
      {
        onSuccess: (data) => setJobSuggestions(data),
      }
    );
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
  const activeResume = resumes.find((r) => r.is_active) || resumes[0];

  return (
    <>
      <Header
        title="Resume Management & AI Optimization"
        subtitle="Upload PDF resumes, run AI quality audits, and generate job-specific tailoring suggestions"
      />

      <PageWrapper>
        <div className="max-w-7xl mx-auto space-y-8 w-full">
          {/* Active Resume Status Banner */}
          {activeResume && (
            <div className="p-5 rounded-2xl bg-success/10 border border-success/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm animate-in fade-in duration-200">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-success/20 text-success flex items-center justify-center shrink-0">
                  <CheckCircle2 size={20} />
                </div>
                <div className="space-y-0.5">
                  <h4 className="text-sm font-bold text-text">Active Resume Registered</h4>
                  <p className="text-xs text-text-secondary">
                    Your active resume <strong className="text-text font-semibold">{activeResume.filename}</strong> is unlocking AI job matching and candidate analytics.
                  </p>
                </div>
              </div>
              <Button
                variant="primary"
                size="sm"
                icon={<Sparkles size={14} />}
                onClick={() => navigate("/jobs")}
                className="shrink-0 text-xs font-semibold shadow-sm"
              >
                Explore Live Jobs <ArrowRight size={14} className="ml-1" />
              </Button>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 w-full">
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

              {/* Active Resume Card */}
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

          {/* AI Resume Quality & Tailoring Section */}
          {activeResume && (
            <div className="space-y-6 pt-4 border-t border-border/40">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-extrabold text-text flex items-center gap-2">
                    <Wand2 className="text-primary" size={22} />
                    AI Resume Quality Audit & Job Tailoring Suite
                  </h2>
                  <p className="text-xs text-text-secondary">
                    Analyze quality, identify missing skills & ATS formatting issues, and generate job-specific recommendations.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Panel 1: Resume Quality Audit */}
                <Card className="flex flex-col justify-between">
                  <div className="space-y-5">
                    <div className="flex items-center justify-between border-b border-border pb-3">
                      <h3 className="text-base font-bold text-text flex items-center gap-2">
                        <ShieldCheck size={18} className="text-success" />
                        Resume Quality Audit
                      </h3>
                      <Button
                        variant="secondary"
                        size="sm"
                        isLoading={qualityAnalysisMutation.isPending}
                        icon={<Zap size={14} />}
                        onClick={() => handleRunQualityAudit(activeResume.id)}
                      >
                        Run Quality Audit
                      </Button>
                    </div>

                    {!qualityAudit ? (
                      <div className="p-8 text-center space-y-2 bg-surface-elevated/30 rounded-xl border border-dashed border-border">
                        <ShieldCheck size={32} className="mx-auto text-text-muted opacity-50" />
                        <p className="text-xs font-semibold text-text">No Quality Audit Executed Yet</p>
                        <p className="text-[11px] text-text-muted">
                          Click "Run Quality Audit" to scan for missing skills, passive descriptions, and ATS issues.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4 animate-in fade-in duration-200">
                        {/* Quality Score Header */}
                        <div className="p-4 rounded-xl bg-surface-elevated border border-border flex items-center justify-between">
                          <div>
                            <span className="text-xs font-bold text-text-muted uppercase tracking-wider block">Quality Score</span>
                            <span className="text-2xl font-black text-primary">{qualityAudit.quality_score}%</span>
                          </div>
                          <Badge
                            variant={qualityAudit.quality_score >= 80 ? "success" : qualityAudit.quality_score >= 65 ? "warning" : "error"}
                            className="font-bold text-xs py-1 px-3"
                          >
                            {qualityAudit.quality_score >= 80 ? "High Quality" : qualityAudit.quality_score >= 65 ? "Moderate Quality" : "Needs Fixes"}
                          </Badge>
                        </div>

                        <p className="text-xs text-text-secondary font-medium leading-relaxed">
                          {qualityAudit.summary}
                        </p>

                        {/* Missing Skills Badges */}
                        {qualityAudit.missing_skills.length > 0 && (
                          <div className="space-y-1.5">
                            <h4 className="text-xs font-bold text-text">Recommended Standard Skills to Add:</h4>
                            <div className="flex flex-wrap gap-1.5">
                              {qualityAudit.missing_skills.map((skill) => (
                                <Badge key={skill} variant="warning" className="text-xs font-semibold">
                                  + {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Weak Descriptions List */}
                        {qualityAudit.weak_descriptions.length > 0 && (
                          <div className="space-y-1.5">
                            <h4 className="text-xs font-bold text-text">Description Action Verbs & Metrics:</h4>
                            <div className="space-y-1">
                              {qualityAudit.weak_descriptions.map((desc, i) => (
                                <div key={i} className="p-2.5 rounded-lg bg-surface-elevated/80 border border-border text-xs text-text-secondary flex items-start gap-2">
                                  <AlertTriangle size={14} className="text-warning shrink-0 mt-0.5" />
                                  <span>{desc}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* ATS Warnings List */}
                        {qualityAudit.ats_issues.length > 0 && (
                          <div className="space-y-1.5">
                            <h4 className="text-xs font-bold text-text">ATS Compliance Warnings:</h4>
                            <div className="space-y-1">
                              {qualityAudit.ats_issues.map((issue, i) => (
                                <div key={i} className="p-2.5 rounded-lg bg-error/10 border border-error/20 text-xs text-error flex items-start gap-2">
                                  <XCircle size={14} className="shrink-0 mt-0.5" />
                                  <span>{issue}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </Card>

                {/* Panel 2: Job-Specific Resume Tailoring */}
                <Card className="flex flex-col justify-between">
                  <div className="space-y-5">
                    <div className="flex items-center justify-between border-b border-border pb-3">
                      <h3 className="text-base font-bold text-text flex items-center gap-2">
                        <Target size={18} className="text-accent" />
                        Job-Specific Tailoring Assistant
                      </h3>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs font-bold text-text mb-1">Target Position Title</label>
                        <Input
                          value={jobTitleInput}
                          onChange={(e) => setJobTitleInput(e.target.value)}
                          placeholder="e.g. Senior Python Developer"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-text mb-1">Target Job Description</label>
                        <textarea
                          value={jobDescInput}
                          onChange={(e) => setJobDescInput(e.target.value)}
                          rows={3}
                          placeholder="Paste target job description text to generate tailored bullet recommendations..."
                          className="w-full px-3 py-2 text-xs rounded-xl bg-surface border border-border focus:ring-2 focus:ring-primary/40 focus:border-primary text-text resize-none"
                        />
                      </div>

                      <Button
                        variant="primary"
                        size="sm"
                        isLoading={jobSuggestionsMutation.isPending}
                        icon={<Sparkles size={14} />}
                        onClick={() => handleRunJobSuggestions(activeResume.id)}
                        className="w-full font-bold"
                      >
                        Generate Tailored Suggestions
                      </Button>
                    </div>

                    {/* Suggestions Results Output */}
                    {jobSuggestions && (
                      <div className="space-y-4 pt-2 border-t border-border animate-in fade-in duration-200">
                        <p className="text-xs text-text font-semibold bg-primary/10 border border-primary/20 p-3 rounded-xl leading-relaxed">
                          {jobSuggestions.tailored_summary}
                        </p>

                        {/* Matching vs Missing Skills */}
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div className="p-3 rounded-xl bg-success/10 border border-success/20 space-y-1">
                            <h5 className="font-bold text-success flex items-center gap-1">
                              <Check size={13} /> Matching Skills ({jobSuggestions.matching_skills.length})
                            </h5>
                            <div className="flex flex-wrap gap-1 pt-1">
                              {jobSuggestions.matching_skills.map((s) => (
                                <Badge key={s} variant="success" className="text-[10px] py-0.5 px-2 font-semibold">
                                  {s}
                                </Badge>
                              ))}
                            </div>
                          </div>

                          <div className="p-3 rounded-xl bg-warning/10 border border-warning/20 space-y-1">
                            <h5 className="font-bold text-warning flex items-center gap-1">
                              <AlertTriangle size={13} /> Required Keywords ({jobSuggestions.missing_job_skills.length})
                            </h5>
                            <div className="flex flex-wrap gap-1 pt-1">
                              {jobSuggestions.missing_job_skills.map((s) => (
                                <Badge key={s} variant="warning" className="text-[10px] py-0.5 px-2 font-semibold">
                                  {s}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Suggested Changes */}
                        {jobSuggestions.suggested_changes.length > 0 && (
                          <div className="space-y-1.5">
                            <h4 className="text-xs font-bold text-text">Recommended Resume Adjustments:</h4>
                            <div className="space-y-1">
                              {jobSuggestions.suggested_changes.map((change, i) => (
                                <div key={i} className="p-2.5 rounded-xl bg-surface-elevated border border-border text-xs text-text-secondary flex items-start gap-2">
                                  <Sparkles size={14} className="text-accent shrink-0 mt-0.5" />
                                  <span>{change}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            </div>
          )}
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
              <div className="p-3 text-xs text-error bg-error/10 border border-error/20 rounded-md">
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
              >
                Delete Permanently
              </Button>
            </div>
          </div>
        </Modal>
      </PageWrapper>
    </>
  );
}

export default ResumePage;

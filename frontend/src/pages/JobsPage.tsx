import { useState } from "react";
import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import JobCard from "../components/shared/JobCard";
import MatchDetails from "../components/shared/MatchDetails";
import EmptyState from "../components/shared/EmptyState";
import SearchBar from "../components/ui/SearchBar";
import ResumeUploader from "../components/shared/ResumeUploader";
import ResumeViewerModal from "../components/profile/ResumeViewerModal";
import AllResumesModal from "../components/shared/AllResumesModal";
import { Spinner, Modal, Button, Badge } from "../components/ui";
import { useJobSearch, useMatchJob, useSuggestedQueries } from "../hooks/useJobs";
import {
  useActiveResume,
  useResumes,
  useUploadResume,
  useSetActiveResume,
  useDeleteResume,
  useParseResume,
} from "../hooks/useResume";
import type { Job, JobSearchQueryParams } from "../types/job";
import type { MatchResult } from "../types/match";
import type { ParsedResumeData } from "../types/resume";
import {
  Search,
  Sparkles,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  Upload,
  User,
  Layers,
  FolderOpen,
} from "lucide-react";

function JobsPage() {
  const [hasSearched, setHasSearched] = useState(false);
  const [queryParams, setQueryParams] = useState<JobSearchQueryParams>({
    query: "",
    location: "",
    remote_only: false,
    limit: 50,
  });

  const [matchesCache, setMatchesCache] = useState<Record<string, MatchResult>>({});
  const [activeModalJob, setActiveModalJob] = useState<Job | null>(null);
  const [activeMatchResult, setActiveMatchResult] = useState<MatchResult | null>(null);
  const [isMatchModalOpen, setIsMatchModalOpen] = useState(false);
  const [isResumeWarningModalOpen, setIsResumeWarningModalOpen] = useState(false);
  const [isPdfViewerOpen, setIsPdfViewerOpen] = useState(false);
  const [isAllResumesModalOpen, setIsAllResumesModalOpen] = useState(false);
  const [showUploader, setShowUploader] = useState(false);
  const [sortByMatch, setSortByMatch] = useState(false);

  // Resume hooks
  const { data: resumesData, isLoading: isResumesLoading } = useResumes();
  const { data: activeResume } = useActiveResume();
  const uploadMutation = useUploadResume();
  const setActiveMutation = useSetActiveResume();
  const deleteMutation = useDeleteResume();
  const parseMutation = useParseResume();

  const resumes = resumesData?.resumes || [];
  const currentActiveResume = activeResume || resumes.find((r) => r.is_active) || resumes[0];
  const hasActiveResume = Boolean(currentActiveResume);

  // Job search hooks
  const { data: searchData, isLoading: isSearchLoading, isError: isSearchError, refetch } = useJobSearch(
    queryParams,
    hasSearched
  );

  const { data: suggestedQueriesData } = useSuggestedQueries();
  const matchMutation = useMatchJob();

  const suggestedQueries = searchData?.suggested_queries?.length
    ? searchData.suggested_queries
    : suggestedQueriesData || [];

  const handleUploadResume = (file: File) => {
    uploadMutation.mutate(file, {
      onSuccess: () => {
        setShowUploader(false);
      },
    });
  };

  const handleSetActiveResume = (resumeId: string) => {
    setActiveMutation.mutate(resumeId);
  };

  const handleDeleteResume = (resumeId: string) => {
    deleteMutation.mutate(resumeId);
  };

  const handleSearch = (filters: {
    query: string;
    location: string;
    remoteOnly?: boolean;
    forceRefresh?: boolean;
  }) => {
    setHasSearched(true);
    setQueryParams({
      query: filters.query,
      location: filters.location,
      remote_only: Boolean(filters.remoteOnly),
      force_refresh: filters.forceRefresh,
      limit: 50,
    });
  };

  const handleMatchClick = (job: Job) => {
    if (!hasActiveResume) {
      setIsResumeWarningModalOpen(true);
      return;
    }

    setActiveModalJob(job);
    setIsMatchModalOpen(true);

    if (matchesCache[job.id]) {
      setActiveMatchResult(matchesCache[job.id]);
    } else {
      matchMutation.mutate(
        { jobId: job.id },
        {
          onSuccess: (result) => {
            setActiveMatchResult(result);
            setMatchesCache((prev) => ({ ...prev, [job.id]: result }));
          },
        }
      );
    }
  };

  const handleApply = (job: Job) => {
    if (job.can_apply && job.apply_url) {
      window.open(job.apply_url, "_blank");
    } else {
      window.open(job.url, "_blank");
    }
  };

  const rawJobs = searchData?.jobs || [];
  const totalJobs = searchData?.total || 0;

  const displayedJobs = [...rawJobs].sort((a, b) => {
    if (!sortByMatch) return 0;
    const scoreA = matchesCache[a.id]?.score ?? a.match_score ?? 0;
    const scoreB = matchesCache[b.id]?.score ?? b.match_score ?? 0;
    return scoreB - scoreA;
  });

  return (
    <>
      <Header
        title="Finder"
        subtitle="Single-page intelligent job discovery engine"
      />

      <PageWrapper>
        <div className="max-w-7xl mx-auto p-6 lg:p-10 space-y-8 min-h-[80vh]">
          
          {/* ========================================================================= */}
          {/* TOP RESUME MANAGER SECTION                                                */}
          {/* ========================================================================= */}
          <section className="bg-surface border border-border rounded-2xl p-6 shadow-sm space-y-4">
            
            {/* STATE 1: No Resume Uploaded */}
            {!hasActiveResume && !isResumesLoading && !uploadMutation.isPending && (
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="space-y-1 text-center md:text-left">
                  <div className="flex items-center justify-center md:justify-start gap-2">
                    <Sparkles className="text-accent" size={20} />
                    <h3 className="text-base font-bold text-text">
                      Upload your resume to enable Search with Resume
                    </h3>
                  </div>
                  <p className="text-xs text-text-secondary">
                    PDF resumes are analyzed to extract skills and generate personalized job recommendations.
                  </p>
                </div>
                <div className="w-full md:w-auto shrink-0">
                  <ResumeUploader
                    onUpload={handleUploadResume}
                    isLoading={uploadMutation.isPending}
                  />
                </div>
              </div>
            )}

            {/* STATE 2: Resume Uploading or Parsing in Progress */}
            {(uploadMutation.isPending || parseMutation.isPending) && (
              <div className="flex items-center justify-center py-8 space-y-2 flex-col">
                <Spinner size="md" />
                <p className="text-sm font-semibold text-text animate-pulse">
                  Analyzing resume... Generating AI search suggestions...
                </p>
              </div>
            )}

            {/* STATE 3: Resume Uploaded & Ready */}
            {hasActiveResume && !uploadMutation.isPending && !parseMutation.isPending && (
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/60 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-success/15 text-success border border-success/30 flex items-center justify-center shrink-0 font-bold">
                      <CheckCircle2 size={20} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-text truncate max-w-xs sm:max-w-md">
                          {currentActiveResume.filename}
                        </h4>
                        <Badge variant="success" className="text-[10px] font-bold">
                          Active Resume ✓
                        </Badge>
                      </div>
                      <p className="text-xs text-text-muted">
                        Active resume for candidate-guided search and AI job fit scoring
                      </p>
                    </div>
                  </div>

                  {/* Resume Manager Buttons: Manage Resumes, View PDF, Upload, Remove */}
                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setIsAllResumesModalOpen(true)}
                      icon={<FolderOpen size={14} />}
                      title="View & manage all uploaded resumes"
                    >
                      Manage Resumes
                    </Button>

                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setIsPdfViewerOpen(true)}
                      icon={<FileText size={14} />}
                    >
                      View PDF
                    </Button>

                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowUploader(!showUploader)}
                      icon={<Upload size={14} />}
                    >
                      {showUploader ? "Cancel" : "Upload"}
                    </Button>

                    <Button
                      variant="danger"
                      size="sm"
                      isLoading={deleteMutation.isPending}
                      onClick={() => handleDeleteResume(currentActiveResume.id)}
                      icon={<Trash2 size={14} />}
                      title="Remove Active Resume"
                    >
                      Remove
                    </Button>
                  </div>
                </div>

                {/* Expandable Upload Dropzone */}
                {showUploader && (
                  <div className="p-4 bg-surface-elevated/40 border border-border rounded-xl">
                    <ResumeUploader
                      onUpload={handleUploadResume}
                      isLoading={uploadMutation.isPending}
                    />
                  </div>
                )}

                {/* Parsed Resume Key Skills Summary */}
                {(() => {
                  const parsed = currentActiveResume.parsed_data as ParsedResumeData | null;
                  if (!parsed) return null;
                  const candidateName = parsed.full_name;
                  const skillsList = Array.isArray(parsed.skills) ? parsed.skills : [];
                  return (
                    <div className="flex flex-wrap items-center gap-4 text-xs pt-1">
                      {candidateName && (
                        <span className="flex items-center gap-1 font-semibold text-text">
                          <User size={13} className="text-primary" />
                          {candidateName}
                        </span>
                      )}

                      {skillsList.length > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-text-muted font-medium flex items-center gap-1">
                            <Layers size={13} className="text-success" /> Extracted Skills:
                          </span>
                          {skillsList.slice(0, 6).map((skillName: string, idx: number) => (
                            <span key={idx} className="bg-surface-elevated border border-border px-2 py-0.5 rounded text-[11px] text-text">
                              {skillName}
                            </span>
                          ))}
                          {skillsList.length > 6 && (
                            <span className="text-[11px] text-text-muted font-medium">
                              +{skillsList.length - 6} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>
            )}
          </section>

          {/* ========================================================================= */}
          {/* SEARCH SECTION & SUGGESTION CHIPS                                         */}
          {/* ========================================================================= */}
          <section className="bg-surface border border-border shadow-sm p-6 rounded-2xl">
            <SearchBar
              onSearch={handleSearch}
              isLoading={isSearchLoading && hasSearched}
              activeResumeFilename={hasActiveResume ? currentActiveResume.filename : null}
              suggestedQueries={suggestedQueries}
              appliedQuery={searchData?.applied_query}
              appliedLocation={searchData?.applied_location}
            />
          </section>

          {/* ========================================================================= */}
          {/* SEARCH RESULTS SECTION                                                    */}
          {/* ========================================================================= */}
          <div className="flex-1">
            {hasSearched ? (
              <>
                {/* Results Toolbar */}
                <section className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-2">
                  <div className="text-sm text-text-secondary">
                    {isSearchLoading ? (
                      <span className="flex items-center gap-2 font-medium">
                        <Spinner size="sm" /> Searching jobs...
                      </span>
                    ) : (
                      <span>
                        Found <strong className="text-text font-bold">{totalJobs}</strong> matching positions
                      </span>
                    )}
                  </div>

                  {rawJobs.length > 0 && (
                    <Button
                      variant={sortByMatch ? "primary" : "secondary"}
                      size="md"
                      onClick={() => {
                        if (!hasActiveResume) {
                          setIsResumeWarningModalOpen(true);
                        } else {
                          setSortByMatch(!sortByMatch);
                        }
                      }}
                      icon={<Sparkles size={16} className={sortByMatch ? "text-white" : "text-primary"} />}
                      className="text-sm font-semibold whitespace-nowrap shadow-sm"
                    >
                      {sortByMatch ? "Sorted by AI Fit" : "Sort by AI Fit"}
                    </Button>
                  )}
                </section>

                {/* Loading Skeletons */}
                {isSearchLoading && (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mt-4">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                      <div key={i} className="h-72 bg-surface-elevated animate-pulse rounded-2xl border border-border" />
                    ))}
                  </div>
                )}

                {/* Error State */}
                {isSearchError && !isSearchLoading && (
                  <div className="p-8 md:p-12 border border-border border-dashed rounded-2xl bg-surface text-center shadow-sm mt-4">
                    <EmptyState
                      icon={<Search size={48} className="mx-auto mb-4 text-error/50" />}
                      title="Search failed"
                      description="Unable to execute search at this time. Please check your backend connection and try again."
                      action={
                        <Button
                          onClick={() => refetch()}
                          variant="primary"
                          className="mt-6"
                        >
                          Retry Search
                        </Button>
                      }
                    />
                  </div>
                )}

                {/* Empty Results State */}
                {!isSearchLoading && !isSearchError && displayedJobs.length === 0 && (
                  <div className="p-8 md:p-12 border border-border border-dashed rounded-2xl bg-surface text-center shadow-sm mt-4">
                    <EmptyState
                      icon={<Search size={48} className="mx-auto mb-4 text-text-muted" />}
                      title="No jobs found"
                      description="Try another keyword, adjust location, or click one of your resume suggestions above."
                    />
                  </div>
                )}

                {/* Jobs Grid */}
                {!isSearchLoading && !isSearchError && displayedJobs.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 auto-rows-fr mt-4">
                    {displayedJobs.map((job) => (
                      <JobCard
                        key={job.id}
                        job={job}
                        match={matchesCache[job.id]}
                        onApply={handleApply}
                        onMatch={handleMatchClick}
                      />
                    ))}
                  </div>
                )}
              </>
            ) : (
              /* Initial Landing Prompt */
              <div className="p-12 text-center border border-border/50 border-dashed rounded-2xl bg-surface/50 space-y-3">
                <Search size={40} className="mx-auto text-text-muted opacity-60" />
                <h3 className="text-lg font-bold text-text">Discover Opportunities</h3>
                <p className="text-xs text-text-secondary max-w-md mx-auto leading-relaxed">
                  Enter a keyword for a <strong>Standard Search</strong>, or click <strong>Search with Resume</strong> to discover positions matched to your profile.
                </p>
              </div>
            )}
          </div>

          {/* Manage All Resumes Modal */}
          <AllResumesModal
            isOpen={isAllResumesModalOpen}
            onClose={() => setIsAllResumesModalOpen(false)}
            resumes={resumes}
            activeResumeId={currentActiveResume?.id}
            onSetActive={handleSetActiveResume}
            onDelete={handleDeleteResume}
            onUpload={handleUploadResume}
            isActivating={setActiveMutation.isPending}
            isDeleting={deleteMutation.isPending}
            isUploading={uploadMutation.isPending}
          />

          {/* AI Match Explanation Modal */}
          <Modal
            isOpen={isMatchModalOpen}
            onClose={() => setIsMatchModalOpen(false)}
            title="AI Job Fit Analysis"
            size="lg"
          >
            {matchMutation.isPending && !activeMatchResult ? (
              <div className="flex flex-col items-center justify-center py-16 space-y-4">
                <Spinner size="lg" />
                <p className="text-sm font-medium text-text-secondary animate-pulse">
                  Analyzing skill overlap and calculating match score...
                </p>
              </div>
            ) : activeModalJob && activeMatchResult ? (
              <MatchDetails
                job={activeModalJob}
                match={activeMatchResult}
                onApply={handleApply}
              />
            ) : null}
          </Modal>

          {/* Missing Resume Warning Modal */}
          <Modal
            isOpen={isResumeWarningModalOpen}
            onClose={() => setIsResumeWarningModalOpen(false)}
            title="Resume Required for AI Fit Analysis"
            size="md"
          >
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-500 flex items-start gap-3">
                <AlertTriangle size={24} className="shrink-0 mt-0.5" />
                <div className="text-xs space-y-1">
                  <p className="font-bold text-sm text-text">Active Resume Missing</p>
                  <p className="text-text-secondary leading-relaxed">
                    AI Job Matching compares candidate resume skills against job requirements. Please upload a PDF resume using the card above.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsResumeWarningModalOpen(false)}
                >
                  Close
                </Button>
              </div>
            </div>
          </Modal>

          {/* Active PDF Viewer Modal */}
          <ResumeViewerModal
            isOpen={isPdfViewerOpen}
            onClose={() => setIsPdfViewerOpen(false)}
            filename={currentActiveResume?.filename || "Active Resume"}
          />
        </div>
      </PageWrapper>
    </>
  );
}

export default JobsPage;

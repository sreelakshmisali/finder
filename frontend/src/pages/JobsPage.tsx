import { useState, useEffect } from "react";
import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import JobCard from "../components/shared/JobCard";
import MatchDetails from "../components/shared/MatchDetails";
import EmptyState from "../components/shared/EmptyState";
import SearchBar from "../components/ui/SearchBar";
import { Badge, Spinner, Modal, Button } from "../components/ui";
import { useNavigate } from "react-router-dom";
import { useJobSearch, useProviders, useMatchJob, useSuggestedQueries } from "../hooks/useJobs";
import { useOnboardingStatus } from "../hooks/useOnboarding";
import type { Job, JobSearchQueryParams, SearchMode } from "../types/job";
import type { MatchResult } from "../types/match";
import { Search, Layers, Sparkles, FileText, AlertTriangle } from "lucide-react";

function JobsPage() {
  const navigate = useNavigate();
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
  const [sortByMatch, setSortByMatch] = useState(false);

  const { data: providersData } = useProviders();
  const { data: searchData, isLoading, isError, refetch } = useJobSearch(
    hasSearched ? queryParams : { ...queryParams, limit: 0 } // Don't trigger full search until hasSearched
  );
  
  // When component mounts, check if we have URL params or state to pre-fill search
  useEffect(() => {
    // Prevent auto-searching on mount unless we have active query params injected
    if (queryParams.query || queryParams.search_mode === "SMART") {
      setHasSearched(true);
    }
  }, [queryParams]);

  const { data: onboarding } = useOnboardingStatus();
  const { data: suggestedQueriesData } = useSuggestedQueries();
  const matchMutation = useMatchJob();

  const hasActiveResume = onboarding?.has_active_resume ?? true;
  const suggestedQueries = searchData?.suggested_queries?.length
    ? searchData.suggested_queries
    : suggestedQueriesData || [];

  const handleSearch = (filters: {
    query: string;
    location: string;
    remoteOnly: boolean;
    sources: string[];
    searchMode: SearchMode;
    minSalary?: number;
    forceRefresh?: boolean;
  }) => {
    setHasSearched(true);
    setQueryParams({
      query: filters.query,
      location: filters.location,
      remote_only: filters.remoteOnly,
      sources: filters.sources,
      search_mode: filters.searchMode,
      min_salary: filters.minSalary,
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
    window.open(job.url, "_blank");
  };

  const handleSkip = (job: Job) => {
    console.log("Skipped job:", job.id);
  };

  const rawJobs = searchData?.jobs || [];
  const totalJobs = searchData?.total || 0;
  const providersSearched = searchData?.providers_searched || [];

  // Sort jobs by match score if toggle is enabled
  const displayedJobs = [...rawJobs].sort((a, b) => {
    if (!sortByMatch) return 0;
    const scoreA = matchesCache[a.id]?.score ?? a.match_score ?? 0;
    const scoreB = matchesCache[b.id]?.score ?? b.match_score ?? 0;
    return scoreB - scoreA;
  });

  return (
    <>
      {hasSearched && (
        <Header
          title="Jobs Discovery & AI Matcher"
          subtitle="Search tech opportunities aggregated concurrently across ATS platforms and rank by resume fit"
          actions={
            providersData && (
              <div className="flex flex-wrap items-center gap-2 mt-4 sm:mt-0">
                <span className="text-sm text-text-secondary flex items-center gap-1.5 font-medium">
                  <Layers size={16} /> Active Sources:
                </span>
                <div className="flex flex-wrap gap-2">
                  {providersData.map((p) => (
                    <Badge key={p.name} variant="default" className="text-xs px-2.5 py-1 bg-surface-elevated">
                      {p.display_name}
                    </Badge>
                  ))}
                </div>
              </div>
            )
          }
        />
      )}

      <PageWrapper>
        <div className={`max-w-7xl mx-auto p-6 lg:p-12 space-y-8 min-h-[80vh] flex flex-col ${!hasSearched ? 'justify-center' : ''}`}>
          
          {/* Missing Resume Warning Banner */}
          {!hasActiveResume && hasSearched && (
            <div className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm animate-in fade-in duration-200">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-amber-500/20 text-amber-500 flex items-center justify-center shrink-0">
                  <AlertTriangle size={20} />
                </div>
                <div className="space-y-0.5">
                  <h4 className="text-sm font-bold text-text">AI Fit Analysis Restricted</h4>
                  <p className="text-xs text-text-secondary">Upload an active PDF resume to unlock personalized skill matching and job fit ranking.</p>
                </div>
              </div>
              <Button
                variant="primary"
                size="sm"
                icon={<FileText size={14} />}
                onClick={() => navigate("/profile")}
                className="shrink-0 text-xs font-semibold shadow-sm"
              >
                Upload Resume
              </Button>
            </div>
          )}

          {/* Search Area */}
          <div className={`transition-all duration-700 ease-in-out ${hasSearched ? "translate-y-0" : "-translate-y-12"}`}>
            {!hasSearched && (
              <div className="text-center mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700 fade-out slide-out-to-top-4">
                <h1 className="text-4xl md:text-5xl font-bold text-text mb-4 tracking-tight">What job are you looking for?</h1>
                <p className="text-text-secondary text-lg max-w-2xl mx-auto">Search exactly what you want, or let your resume do the work to find the perfect role.</p>
              </div>
            )}
            
            <section className={`transition-all duration-700 ease-in-out ${hasSearched ? "bg-surface border border-border shadow-sm p-4 sm:p-6 rounded-2xl sticky top-4 z-10" : ""}`}>
              <SearchBar
                onSearch={handleSearch}
                isLoading={isLoading && hasSearched}
                providers={providersData}
                suggestedQueries={suggestedQueries}
                appliedQuery={searchData?.applied_query}
                appliedLocation={searchData?.applied_location}
                layout={hasSearched ? "header" : "landing"}
              />
            </section>
          </div>

          <div className={`transition-all duration-700 ease-in-out flex-1 ${hasSearched ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12 h-0 overflow-hidden"}`}>
            {hasSearched && (
              <>
                {/* Results Toolbar */}
                <section className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-2 mt-2">
                  <div className="text-sm text-text-secondary">
                    {isLoading ? (
                      <span className="flex items-center gap-2 font-medium">
                        <Spinner size="sm" /> Searching across job providers...
                      </span>
                    ) : (
                      <span>
                        Found <strong className="text-text font-bold">{totalJobs}</strong> matching positions
                        {providersSearched.length > 0 && (
                          <span className="text-text-muted ml-1">
                            from {providersSearched.join(", ")}
                          </span>
                        )}
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
                {isLoading && (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mt-4">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                      <div key={i} className="h-72 bg-surface-elevated animate-pulse rounded-2xl border border-border" />
                    ))}
                  </div>
                )}

                {/* Error State */}
                {isError && !isLoading && (
                  <div className="p-8 md:p-12 border border-border border-dashed rounded-2xl bg-surface text-center shadow-sm mt-4">
                    <EmptyState
                      icon={<Search size={48} className="mx-auto mb-4 text-error/50" />}
                      title="Search failed"
                      description="Unable to query job providers at this time. Please ensure the backend service is active and try again."
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

                {/* Empty State */}
                {!isLoading && !isError && displayedJobs.length === 0 && (
                  <div className="p-8 md:p-12 border border-border border-dashed rounded-2xl bg-surface text-center shadow-sm mt-4">
                    <EmptyState
                      icon={<Search size={48} className="mx-auto mb-4 text-text-muted" />}
                      title="No jobs found"
                      description="Try adjusting your search keywords or location filters to discover open positions."
                    />
                  </div>
                )}

                {/* Jobs Grid */}
                {!isLoading && !isError && displayedJobs.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 auto-rows-fr mt-4">
                    {displayedJobs.map((job) => (
                      <JobCard
                        key={job.id}
                        job={job}
                        match={matchesCache[job.id]}
                        onApply={handleApply}
                        onSkip={handleSkip}
                        onMatch={handleMatchClick}
                      />
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

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
                  Analyzing skill overlap and generating AI insights...
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

          {/* Resume Required Alert Modal */}
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
                    AI Job Matching compares candidate resume skills against job requirements. Please upload an active PDF resume to enable personalized scoring.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsResumeWarningModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setIsResumeWarningModalOpen(false);
                    navigate("/profile");
                  }}
                  icon={<FileText size={14} />}
                >
                  Upload Resume
                </Button>
              </div>
            </div>
          </Modal>
        </div>
      </PageWrapper>
    </>
  );
}

export default JobsPage;

import { useState } from "react";
import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import JobCard from "../components/shared/JobCard";
import MatchDetails from "../components/shared/MatchDetails";
import EmptyState from "../components/shared/EmptyState";
import SearchBar from "../components/ui/SearchBar";
import { Badge, Spinner, Modal, Button } from "../components/ui";
import { useJobSearch, useProviders, useMatchJob } from "../hooks/useJobs";
import type { Job, JobSearchQueryParams } from "../types/job";
import type { MatchResult } from "../types/match";
import { Search, Layers, Sparkles } from "lucide-react";

function JobsPage() {
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
  const [sortByMatch, setSortByMatch] = useState(false);

  const { data: providersData } = useProviders();
  const { data: searchData, isLoading, isError, refetch } = useJobSearch(queryParams);
  const matchMutation = useMatchJob();

  const handleSearch = (filters: { query: string; location: string; remoteOnly: boolean; sources: string[] }) => {
    setQueryParams({
      query: filters.query,
      location: filters.location,
      remote_only: filters.remoteOnly,
      sources: filters.sources,
      limit: 50,
    });
  };

  const handleMatchClick = (job: Job) => {
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

      <PageWrapper>
        <div className="max-w-7xl mx-auto p-6 lg:p-12 space-y-8">
          {/* Search & Filter Bar */}
          <section className="bg-surface border border-border shadow-sm p-4 sm:p-6 rounded-2xl">
            <SearchBar
              onSearch={handleSearch}
              isLoading={isLoading}
              providers={providersData}
            />
          </section>

          {/* Results Toolbar */}
          <section className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-2">
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
                onClick={() => setSortByMatch(!sortByMatch)}
                icon={<Sparkles size={16} className={sortByMatch ? "text-white" : "text-primary"} />}
                className="text-sm font-semibold whitespace-nowrap shadow-sm"
              >
                {sortByMatch ? "Sorted by AI Fit" : "Sort by AI Fit"}
              </Button>
            )}
          </section>

          {/* Loading Skeletons */}
          {isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-72 bg-surface-elevated animate-pulse rounded-2xl border border-border" />
              ))}
            </div>
          )}

          {/* Error State */}
          {isError && !isLoading && (
            <div className="p-8 md:p-12 border border-border border-dashed rounded-2xl bg-surface text-center shadow-sm">
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
            <div className="p-8 md:p-12 border border-border border-dashed rounded-2xl bg-surface text-center shadow-sm">
              <EmptyState
                icon={<Search size={48} className="mx-auto mb-4 text-text-muted" />}
                title="No jobs found"
                description="Try adjusting your search keywords or location filters to discover open positions."
              />
            </div>
          )}

          {/* Jobs Grid */}
          {!isLoading && !isError && displayedJobs.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 auto-rows-fr">
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
        </div>
      </PageWrapper>
    </>
  );
}

export default JobsPage;

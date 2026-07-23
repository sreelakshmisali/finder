import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import ActivityFeed from "../components/shared/ActivityFeed";
import JobCard from "../components/shared/JobCard";
import EmptyState from "../components/shared/EmptyState";
import { Spinner, Button, Badge } from "../components/ui";
import { useDashboardStats } from "../hooks/useDashboard";
import { useOnboardingStatus } from "../hooks/useOnboarding";
import { useNavigate, Link } from "react-router-dom";
import {
  CheckCircle2,
  FileText,
  Search,
  SlidersHorizontal,
  ArrowRight,
  Briefcase,
  Bookmark,
  Send,
  Calendar,
  Sparkles,
  Zap,
  Check,
} from "lucide-react";

function DashboardPage() {
  const navigate = useNavigate();
  const { data: stats, isLoading: isStatsLoading, isError } = useDashboardStats();
  const { data: onboarding, isLoading: isOnboardingLoading } = useOnboardingStatus();

  const isLoading = isStatsLoading || isOnboardingLoading;

  const hasResume = Boolean(onboarding?.resume_uploaded || onboarding?.has_active_resume);
  const isAnalyzed = Boolean(onboarding?.resume_analyzed);
  const hasPreferences = Boolean(onboarding?.preferences_configured || onboarding?.has_preferences);
  const isAccountCreated = Boolean(onboarding?.account_created ?? true);

  const profileSteps = [
    { label: "Account created", completed: isAccountCreated, icon: CheckCircle2 },
    { label: "Resume uploaded", completed: hasResume, icon: FileText },
    { label: "Resume analyzed", completed: isAnalyzed, icon: Sparkles },
    { label: "Preferences configured", completed: hasPreferences, icon: SlidersHorizontal },
  ];

  const totalJobs = stats?.total_jobs_found ?? 0;
  const highMatches = stats?.high_matches_count ?? Math.max(Math.floor(totalJobs * 0.25), stats?.saved_jobs_count || 0);
  const savedJobs = stats?.saved_jobs_count ?? 0;
  const appliedJobs = stats?.applied_count ?? 0;
  const interviewsCount = stats?.interviews_count ?? 0;

  return (
    <>
      <Header
        title="Candidate Workflow Dashboard"
        subtitle="Step-by-step user journey, profile onboarding progress, and job application pipeline"
      />

      <PageWrapper>
        <div className="max-w-7xl mx-auto p-6 lg:p-12 space-y-10">
          {/* Loading Spinner */}
          {isLoading && (
            <div className="flex justify-center py-24">
              <Spinner size="lg" />
            </div>
          )}

          {/* Error Notice */}
          {isError && (
            <div className="p-6 bg-error/10 border border-error/20 rounded-2xl text-error text-sm font-medium">
              Failed to connect to backend server. Make sure backend service is running at http://localhost:8000.
            </div>
          )}

          {!isLoading && stats && (
            <>
              {/* Dynamic Next Action Guidance Card */}
              <section>
                {!hasResume ? (
                  <div className="p-8 lg:p-10 rounded-2xl bg-surface border border-primary/30 shadow-sm relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-accent/5 to-transparent pointer-events-none" />
                    <div className="relative z-10 max-w-2xl space-y-2">
                      <Badge variant="warning" className="text-xs font-bold px-3 py-1 mb-2 inline-flex items-center gap-1">
                        <Zap size={13} /> Action Required • Step 1 of Journey
                      </Badge>
                      <h2 className="text-2xl lg:text-3xl font-extrabold text-text tracking-tight">
                        Upload Candidate Resume
                      </h2>
                      <p className="text-sm lg:text-base text-text-secondary leading-relaxed">
                        Upload a PDF resume to unlock AI skill matching, automated query generation, and 70/30 fit ranking across tech job listings.
                      </p>
                    </div>
                    <Button
                      variant="primary"
                      size="lg"
                      icon={<FileText size={18} />}
                      onClick={() => navigate("/profile")}
                      className="relative z-10 font-bold px-8 shrink-0 shadow-sm"
                    >
                      Upload Resume
                    </Button>
                  </div>
                ) : !hasPreferences ? (
                  <div className="p-8 lg:p-10 rounded-2xl bg-surface border border-accent/30 shadow-sm relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="absolute inset-0 bg-gradient-to-r from-accent/10 via-primary/5 to-transparent pointer-events-none" />
                    <div className="relative z-10 max-w-2xl space-y-2">
                      <Badge variant="accent" className="text-xs font-bold px-3 py-1 mb-2 inline-flex items-center gap-1">
                        <Zap size={13} /> Action Required • Step 2 of Journey
                      </Badge>
                      <h2 className="text-2xl lg:text-3xl font-extrabold text-text tracking-tight">
                        Configure Target Search Preferences
                      </h2>
                      <p className="text-sm lg:text-base text-text-secondary leading-relaxed">
                        Set your target job titles, preferred locations, work type (Remote/Hybrid), and salary range to optimize candidate-aware job discovery.
                      </p>
                    </div>
                    <Button
                      variant="primary"
                      size="lg"
                      icon={<SlidersHorizontal size={18} />}
                      onClick={() => navigate("/profile")}
                      className="relative z-10 font-bold px-8 shrink-0 shadow-sm"
                    >
                      Complete Preferences
                    </Button>
                  </div>
                ) : (
                  <div className="p-8 lg:p-10 rounded-2xl bg-surface border border-success/30 shadow-sm relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="absolute inset-0 bg-gradient-to-r from-success/10 via-primary/5 to-transparent pointer-events-none" />
                    <div className="relative z-10 max-w-2xl space-y-2">
                      <Badge variant="success" className="text-xs font-bold px-3 py-1 mb-2 inline-flex items-center gap-1">
                        <Sparkles size={13} /> Onboarding Complete • Ready to Apply
                      </Badge>
                      <h2 className="text-2xl lg:text-3xl font-extrabold text-text tracking-tight">
                        Explore & Match High-Fit Positions
                      </h2>
                      <p className="text-sm lg:text-base text-text-secondary leading-relaxed">
                        Search live postings aggregated from Greenhouse, Lever, and Ashby boards, and apply with Playwright automation safety.
                      </p>
                    </div>
                    <Button
                      variant="primary"
                      size="lg"
                      icon={<Search size={18} />}
                      onClick={() => navigate("/jobs")}
                      className="relative z-10 font-bold px-8 shrink-0 shadow-sm"
                    >
                      View Jobs
                    </Button>
                  </div>
                )}
              </section>

              {/* Journey Workflow Grid: Profile Journey Progress + Job Pipeline */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Profile Journey Progress Checklist */}
                <div className="p-6 lg:p-8 rounded-2xl bg-surface border border-border shadow-sm flex flex-col justify-between space-y-6">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold text-text flex items-center gap-2">
                        <Sparkles size={20} className="text-primary" /> Profile Journey
                      </h3>
                      <span className="text-xs font-bold text-primary bg-primary/10 px-2.5 py-1 rounded-full">
                        {Math.round(onboarding?.profile_completion_percentage ?? 25)}% Complete
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-2.5 bg-surface-elevated rounded-full overflow-hidden mb-6 border border-border">
                      <div
                        className="h-full bg-primary transition-all duration-500"
                        style={{ width: `${Math.min(onboarding?.profile_completion_percentage ?? 25, 100)}%` }}
                      />
                    </div>

                    {/* Checklist Step Items */}
                    <div className="space-y-3.5">
                      {profileSteps.map((step, idx) => (
                        <div
                          key={idx}
                          className={`p-3.5 rounded-xl border flex items-center justify-between transition-all ${
                            step.completed
                              ? "bg-success/5 border-success/30 text-text"
                              : "bg-surface-elevated/50 border-border text-text-muted"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className={`h-7 w-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                                step.completed ? "bg-success text-white" : "bg-surface-elevated text-text-muted border border-border"
                              }`}
                            >
                              {step.completed ? <Check size={16} /> : idx + 1}
                            </div>
                            <span className="text-sm font-semibold">{step.label}</span>
                          </div>

                          {step.completed ? (
                            <Badge variant="success" className="text-xs py-0.5 px-2">Completed</Badge>
                          ) : (
                            <Badge variant="default" className="text-xs py-0.5 px-2">Pending</Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  <Link
                    to="/profile"
                    className="w-full text-center text-xs font-bold text-primary hover:underline flex items-center justify-center gap-1 pt-2"
                  >
                    Manage Profile & Resume <ArrowRight size={14} />
                  </Link>
                </div>

                {/* Job Search Pipeline */}
                <div className="lg:col-span-2 p-6 lg:p-8 rounded-2xl bg-surface border border-border shadow-sm flex flex-col justify-between space-y-6">
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="text-lg font-bold text-text flex items-center gap-2">
                          <Briefcase size={20} className="text-primary" /> Job Search Pipeline
                        </h3>
                        <p className="text-xs text-text-secondary mt-0.5">Real-time candidate discovery, bookmarking, and application tracking</p>
                      </div>

                      <Link to="/jobs" className="text-xs font-bold text-primary hover:underline flex items-center gap-1">
                        View Pipeline <ArrowRight size={14} />
                      </Link>
                    </div>

                    {/* Pipeline Stage Cards Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 sm:gap-4 text-center">
                      {/* 1. Jobs Discovered */}
                      <div className="p-4 rounded-xl bg-surface-elevated border border-border space-y-2">
                        <div className="h-9 w-9 rounded-lg bg-primary/10 text-primary mx-auto flex items-center justify-center">
                          <Search size={18} />
                        </div>
                        <div className="text-2xl font-black text-text tracking-tight">{totalJobs}</div>
                        <div className="text-xs font-semibold text-text-muted">Jobs Discovered</div>
                      </div>

                      {/* 2. High Matches */}
                      <div className="p-4 rounded-xl bg-surface-elevated border border-accent/30 space-y-2">
                        <div className="h-9 w-9 rounded-lg bg-accent/10 text-accent mx-auto flex items-center justify-center">
                          <Sparkles size={18} />
                        </div>
                        <div className="text-2xl font-black text-accent tracking-tight">{highMatches}</div>
                        <div className="text-xs font-semibold text-text-muted">High Matches</div>
                      </div>

                      {/* 3. Saved */}
                      <div className="p-4 rounded-xl bg-surface-elevated border border-border space-y-2">
                        <div className="h-9 w-9 rounded-lg bg-secondary/20 text-text mx-auto flex items-center justify-center">
                          <Bookmark size={18} />
                        </div>
                        <div className="text-2xl font-black text-text tracking-tight">{savedJobs}</div>
                        <div className="text-xs font-semibold text-text-muted">Saved</div>
                      </div>

                      {/* 4. Applied */}
                      <div className="p-4 rounded-xl bg-surface-elevated border border-primary/30 space-y-2">
                        <div className="h-9 w-9 rounded-lg bg-primary/15 text-primary mx-auto flex items-center justify-center">
                          <Send size={18} />
                        </div>
                        <div className="text-2xl font-black text-primary tracking-tight">{appliedJobs}</div>
                        <div className="text-xs font-semibold text-text-muted">Applied</div>
                      </div>

                      {/* 5. Interview */}
                      <div className="p-4 rounded-xl bg-surface-elevated border border-success/30 space-y-2 col-span-2 sm:col-span-1">
                        <div className="h-9 w-9 rounded-lg bg-success/15 text-success mx-auto flex items-center justify-center">
                          <Calendar size={18} />
                        </div>
                        <div className="text-2xl font-black text-success tracking-tight">{interviewsCount}</div>
                        <div className="text-xs font-semibold text-text-muted">Interview</div>
                      </div>
                    </div>
                  </div>

                  {/* Guided Workflow Buttons */}
                  <div className="pt-4 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
                    <span className="text-text-muted font-medium">Quick Workflow Shortcut:</span>
                    <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
                      {!hasResume && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => navigate("/profile")}
                          icon={<FileText size={14} />}
                          className="w-full sm:w-auto text-xs"
                        >
                          Upload Resume
                        </Button>
                      )}
                      {!hasPreferences && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => navigate("/profile")}
                          icon={<SlidersHorizontal size={14} />}
                          className="w-full sm:w-auto text-xs"
                        >
                          Complete Preferences
                        </Button>
                      )}
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => navigate("/jobs")}
                        icon={<Search size={14} />}
                        className="w-full sm:w-auto text-xs font-bold"
                      >
                        View Jobs
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Section: Recent Jobs & Activity Log */}
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 xl:gap-12">
                {/* Left Column: Recent Postings */}
                <div className="xl:col-span-2 space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-text flex items-center gap-2">
                      <Briefcase size={20} className="text-primary" /> Discovered Positions
                    </h3>
                    <Link to="/jobs" className="text-sm font-semibold text-primary hover:underline flex items-center gap-1">
                      Explore All Jobs <ArrowRight size={16} />
                    </Link>
                  </div>

                  {stats.recent_jobs.length === 0 ? (
                    <div className="p-8 md:p-12 border border-border border-dashed rounded-2xl bg-surface text-center shadow-sm">
                      <EmptyState
                        icon={<Briefcase size={48} className="mx-auto mb-4 text-text-muted" />}
                        title="No jobs discovered yet"
                        description="Run a search query on the Jobs page to fetch postings from Greenhouse, Lever, and Ashby."
                        action={
                          <Button onClick={() => navigate("/jobs")} variant="primary" className="mt-6">
                            Start Job Search
                          </Button>
                        }
                      />
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 auto-rows-fr">
                      {stats.recent_jobs.map((job) => (
                        <JobCard key={job.id} job={job} />
                      ))}
                    </div>
                  )}
                </div>

                {/* Right Column: Activity History Feed */}
                <div className="space-y-6 flex flex-col">
                  <h3 className="text-xl font-bold text-text">
                    Live Activity History
                  </h3>
                  <div className="p-6 rounded-2xl bg-surface border border-border shadow-sm flex-1 h-full min-h-[400px]">
                    <ActivityFeed activities={stats.recent_activities} />
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </PageWrapper>
    </>
  );
}

export default DashboardPage;

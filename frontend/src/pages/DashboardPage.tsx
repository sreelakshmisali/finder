import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import StatCard from "../components/shared/StatCard";
import ActivityFeed from "../components/shared/ActivityFeed";
import JobCard from "../components/shared/JobCard";
import EmptyState from "../components/shared/EmptyState";
import { Spinner } from "../components/ui";
import { useDashboardStats } from "../hooks/useDashboard";
import {
  Briefcase,
  FileText,
  Sparkles,
  ClipboardList,
  Search,
  SlidersHorizontal,
  ArrowRight,
  Zap,
} from "lucide-react";
import { Link } from "react-router-dom";

function DashboardPage() {
  const { data: stats, isLoading, isError } = useDashboardStats();

  return (
    <>
      <Header
        title="Dashboard"
        subtitle="AI-powered job discovery, resume matching, and application automation overview"
      />

      <PageWrapper>
        <div className="max-w-7xl mx-auto p-6 lg:p-12 space-y-12">
          {/* Hero Banner */}
          <div className="relative overflow-hidden p-8 lg:p-12 rounded-2xl bg-surface border border-border shadow-sm">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-accent/5 to-transparent pointer-events-none" />
            <div className="max-w-3xl relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-xs font-semibold text-primary mb-6">
                <Zap size={14} /> Playwright & AI Match Engine Online
              </div>
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-black text-text tracking-tight mb-4 leading-tight">
                Accelerate Your Job Search with <span className="text-primary">Finder AI</span>
              </h2>
              <p className="text-base lg:text-lg text-text-secondary leading-relaxed mb-8 max-w-2xl">
                Search real-time Greenhouse, Lever, and Ashby postings, analyze 70/30 skill alignment, and fill applications with human confirmation safety.
              </p>

              <div className="flex flex-col sm:flex-row flex-wrap items-center gap-4">
                <Link
                  to="/jobs"
                  className="px-6 py-3 rounded-xl bg-primary text-white font-semibold text-sm hover:bg-primary-hover shadow-sm transition-all flex items-center justify-center gap-2 w-full sm:w-auto"
                >
                  <Search size={18} /> Explore New Listings
                </Link>
                <Link
                  to="/resume"
                  className="px-6 py-3 rounded-xl bg-surface-elevated border border-border font-semibold text-sm text-text hover:bg-surface-hover shadow-sm transition-all flex items-center justify-center gap-2 w-full sm:w-auto"
                >
                  <FileText size={18} /> Manage Resume
                </Link>
              </div>
            </div>
          </div>

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
            <div className="space-y-12">
              {/* Metric Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                  title="Jobs Discovered"
                  value={stats.total_jobs_found}
                  icon={<Briefcase size={24} />}
                  trend="+12 fetched"
                />
                <StatCard
                  title="Saved Jobs"
                  value={stats.saved_jobs_count}
                  icon={<FileText size={24} />}
                  trend="Bookmarked"
                />
                <StatCard
                  title="AI Match Score"
                  value="88%"
                  icon={<Sparkles size={24} />}
                  trend="Top Alignment"
                />
                <StatCard
                  title="Tracked Applications"
                  value={stats.applied_count}
                  icon={<ClipboardList size={24} />}
                  trend="Live Tracking"
                />
              </div>

              {/* Quick Actions Grid */}
              <section>
                <h3 className="text-xl font-bold text-text mb-6">
                  Quick Workflows
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Link to="/jobs" className="group h-full">
                    <div className="p-6 h-full rounded-2xl bg-surface border border-border shadow-sm hover:shadow-md hover:border-primary/30 transition-all flex flex-col">
                      <div className="flex items-center justify-between mb-4">
                        <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center transition-transform group-hover:scale-105">
                          <Search size={24} />
                        </div>
                        <ArrowRight size={20} className="text-text-muted group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </div>
                      <h4 className="font-bold text-text text-base mb-2">Search & Discover Jobs</h4>
                      <p className="text-sm text-text-secondary leading-relaxed flex-1">
                        Fetch live postings from Greenhouse, Lever, and Ashby ATS boards.
                      </p>
                    </div>
                  </Link>

                  <Link to="/resume" className="group h-full">
                    <div className="p-6 h-full rounded-2xl bg-surface border border-border shadow-sm hover:shadow-md hover:border-accent/30 transition-all flex flex-col">
                      <div className="flex items-center justify-between mb-4">
                        <div className="h-12 w-12 rounded-xl bg-accent/10 text-accent flex items-center justify-center transition-transform group-hover:scale-105">
                          <FileText size={24} />
                        </div>
                        <ArrowRight size={20} className="text-text-muted group-hover:text-accent group-hover:translate-x-1 transition-all" />
                      </div>
                      <h4 className="font-bold text-text text-base mb-2">Parse & Activate Resume</h4>
                      <p className="text-sm text-text-secondary leading-relaxed flex-1">
                        Upload PDF resume to extract skills, experience, and contact info.
                      </p>
                    </div>
                  </Link>

                  <Link to="/preferences" className="group h-full">
                    <div className="p-6 h-full rounded-2xl bg-surface border border-border shadow-sm hover:shadow-md hover:border-success/30 transition-all flex flex-col">
                      <div className="flex items-center justify-between mb-4">
                        <div className="h-12 w-12 rounded-xl bg-success/10 text-success flex items-center justify-center transition-transform group-hover:scale-105">
                          <SlidersHorizontal size={24} />
                        </div>
                        <ArrowRight size={20} className="text-text-muted group-hover:text-success group-hover:translate-x-1 transition-all" />
                      </div>
                      <h4 className="font-bold text-text text-base mb-2">Configure Target Fit</h4>
                      <p className="text-sm text-text-secondary leading-relaxed flex-1">
                        Set target role titles, locations, remote options, and salary expectations.
                      </p>
                    </div>
                  </Link>
                </div>
              </section>

              {/* Two Column Grid: Activity Feed + Latest Jobs */}
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 xl:gap-12">
                {/* Left Column: Latest Jobs Grid */}
                <div className="xl:col-span-2 space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-text">
                      Recent Job Listings
                    </h3>
                    <Link to="/jobs" className="text-sm font-medium text-primary hover:text-primary-hover flex items-center gap-1 transition-colors">
                      View All <ArrowRight size={16} />
                    </Link>
                  </div>

                  {stats.recent_jobs.length === 0 ? (
                    <div className="p-8 md:p-12 border border-border border-dashed rounded-2xl bg-surface text-center shadow-sm">
                      <EmptyState
                        icon={<Briefcase size={48} className="mx-auto mb-4 text-text-muted" />}
                        title="No jobs fetched yet"
                        description="Run a job search query to discover live postings from tech job boards."
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

                {/* Right Column: Activity Feed */}
                <div className="space-y-6 flex flex-col">
                  <h3 className="text-xl font-bold text-text">
                    Live Activity History
                  </h3>
                  <div className="p-6 rounded-2xl bg-surface border border-border shadow-sm flex-1 h-full min-h-[400px]">
                    <ActivityFeed activities={stats.recent_activities} />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </PageWrapper>
    </>
  );
}

export default DashboardPage;

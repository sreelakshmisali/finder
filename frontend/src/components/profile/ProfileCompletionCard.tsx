/**
 * ProfileCompletionCard Component
 *
 * Displays overall candidate profile setup status with separate badges for
 * Resume (Required Capability) and Job Preferences (Optional Goals).
 */

import { CheckCircle2, AlertCircle, FileText, SlidersHorizontal, Sparkles } from "lucide-react";
import type { ProfileSetupData } from "../../types/profile";
import { Badge } from "../ui";

interface ProfileCompletionCardProps {
  data?: ProfileSetupData;
}

export default function ProfileCompletionCard({ data }: ProfileCompletionCardProps) {
  const resumeCompleted = data?.resume_completed ?? false;
  const preferencesCompleted = data?.preferences_completed ?? false;
  const percentage = data?.profile_completion_percentage ?? 20;

  return (
    <div className="relative overflow-hidden p-6 sm:p-8 rounded-3xl bg-surface border border-border shadow-md space-y-6">
      {/* Background Gradient Accent */}
      <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Header & Score Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-bold text-primary mb-2">
            <Sparkles size={14} /> Profile Readiness Center
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-text tracking-tight">
            Candidate <span className="text-primary">Profile Setup</span>
          </h2>
          <p className="text-sm text-text-secondary">
            Resume defines your candidate capabilities. Preferences specify your target career goals.
          </p>
        </div>

        {/* Progress Metric Ring / Pill */}
        <div className="flex items-center gap-4 bg-surface-elevated/70 p-4 rounded-2xl border border-border/60 shrink-0">
          <div className="space-y-1 text-right">
            <span className="text-xs uppercase font-bold text-text-muted tracking-wider block">
              Setup Completion
            </span>
            <div className="text-2xl font-black text-primary">
              {Math.round(percentage)}%
            </div>
          </div>
          <div className="w-24 bg-surface rounded-full h-3 overflow-hidden border border-border/80">
            <div
              className="bg-gradient-to-r from-primary to-accent h-full transition-all duration-500 rounded-full"
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Status Badges Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative z-10 pt-2">
        {/* Resume Status Card */}
        <a
          href="#resume-section"
          className="p-4 rounded-2xl bg-surface-elevated/40 border border-border hover:border-primary/40 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center gap-3">
            <div
              className={`h-10 w-10 rounded-xl flex items-center justify-center shrink-0 ${
                resumeCompleted
                  ? "bg-success/15 text-success"
                  : "bg-amber-500/15 text-amber-500"
              }`}
            >
              {resumeCompleted ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-text">1. PDF Resume</span>
                <Badge variant="error" className="text-[10px] uppercase font-bold px-2 py-0.5">
                  Required
                </Badge>
              </div>
              <p className="text-xs text-text-secondary mt-0.5">
                {resumeCompleted
                  ? "Uploaded & parsed for AI job matching"
                  : "Action required: Upload PDF resume"}
              </p>
            </div>
          </div>
          <FileText size={18} className="text-text-muted group-hover:text-primary transition-colors" />
        </a>

        {/* Preferences Status Card */}
        <a
          href="#preferences-section"
          className="p-4 rounded-2xl bg-surface-elevated/40 border border-border hover:border-accent/40 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center gap-3">
            <div
              className={`h-10 w-10 rounded-xl flex items-center justify-center shrink-0 ${
                preferencesCompleted
                  ? "bg-success/15 text-success"
                  : "bg-primary/10 text-primary"
              }`}
            >
              {preferencesCompleted ? (
                <CheckCircle2 size={20} />
              ) : (
                <SlidersHorizontal size={20} />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-text">2. Job Preferences</span>
                <Badge variant="default" className="text-[10px] uppercase font-bold px-2 py-0.5 bg-surface-elevated">
                  Optional
                </Badge>
              </div>
              <p className="text-xs text-text-secondary mt-0.5">
                {preferencesCompleted
                  ? "Configured target roles, locations & salary"
                  : "Optional: Skip or configure target fit criteria"}
              </p>
            </div>
          </div>
          <SlidersHorizontal size={18} className="text-text-muted group-hover:text-accent transition-colors" />
        </a>
      </div>
    </div>
  );
}

import type { MatchResult } from "../../types/match";
import type { Job } from "../../types/job";
import { Badge, Button } from "../ui";
import { Sparkles, CheckCircle2, AlertCircle, ExternalLink, Zap } from "lucide-react";

interface MatchDetailsProps {
  job: Job;
  match: MatchResult;
  onApply?: (job: Job) => void;
}

function MatchDetails({ job, match, onApply }: MatchDetailsProps) {
  let variant: "success" | "warning" | "error" | "primary" = "success";
  if (match.score < 50) variant = "error";
  else if (match.score < 80) variant = "warning";
  else if (match.score >= 90) variant = "primary";

  return (
    <div className="space-y-6">
      {/* Job Title & Company Header */}
      <div className="p-5 bg-surface border border-border shadow-sm rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-text mb-1">{job.title}</h3>
          <p className="text-sm text-primary font-medium">{job.company} <span className="text-text-muted mx-1">•</span> {job.location}</p>
        </div>

        <div className="shrink-0">
          <Badge variant={variant} className="text-base px-4 py-1.5 font-bold shadow-sm">
            ⚡ {Math.round(match.score)}% Match
          </Badge>
        </div>
      </div>

      {/* AI Recommendation Banner */}
      <div className="p-5 rounded-2xl bg-primary/5 border border-primary/20 flex items-start gap-4">
        <div className="p-2 bg-primary/10 rounded-xl shrink-0">
          <Sparkles size={24} className="text-primary" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-text mb-1.5">
            AI Recommendation
          </h4>
          <p className="text-sm text-text-secondary leading-relaxed">
            {match.recommendation}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Positive Matching Reasons */}
        {match.reasons && match.reasons.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
              <CheckCircle2 size={18} className="text-success" /> Key Strengths ({match.reasons.length})
            </h4>
            <div className="space-y-2">
              {match.reasons.map((reason, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-surface border border-border shadow-sm text-sm text-text-secondary flex items-start gap-3"
                >
                  <span className="text-success font-bold mt-0.5">✓</span>
                  <span className="leading-relaxed">{reason}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Missing Skills */}
        {match.missing_skills && match.missing_skills.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
              <AlertCircle size={18} className="text-warning" /> Missing Skills ({match.missing_skills.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {match.missing_skills.map((skill, i) => (
                <Badge key={i} variant="warning" className="px-3 py-1.5 text-sm font-medium shadow-sm">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Raw Score Math Breakdown */}
      {match.score_breakdown && (
        <div className="p-5 rounded-2xl bg-surface border border-border shadow-sm flex items-center justify-around text-center mt-2">
          <div className="flex-1">
            <span className="text-xs font-semibold text-text-muted uppercase tracking-wider block mb-1">Keyword Overlap</span>
            <span className="font-bold text-text text-xl">
              {match.score_breakdown.keyword_score}%
            </span>
          </div>
          <div className="h-12 w-px bg-border mx-4" />
          <div className="flex-1">
            <span className="text-xs font-semibold text-text-muted uppercase tracking-wider block mb-1">Preference Fit</span>
            <span className="font-bold text-primary text-xl">
              +{match.score_breakdown.preference_bonus} pts
            </span>
          </div>
        </div>
      )}

      {/* Footer Action Buttons */}
      <div className="pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-primary transition-colors p-2"
        >
          View Original Listing <ExternalLink size={16} />
        </a>

        {onApply && (
          <Button variant="primary" size="lg" onClick={() => onApply(job)} icon={<Zap size={18} />} className="w-full sm:w-auto font-bold px-8 shadow-sm">
            Approve & Apply
          </Button>
        )}
      </div>
    </div>
  );
}

export default MatchDetails;

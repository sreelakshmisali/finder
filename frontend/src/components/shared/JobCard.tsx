import type { Job } from "../../types/job";
import type { MatchResult } from "../../types/match";
import MatchBadge from "./MatchBadge";
import Badge from "../ui/Badge";
import { Button } from "../ui";
import { Building2, MapPin, ExternalLink, Sparkles, Bookmark } from "lucide-react";
import { getInitials, stripHtml } from "../../lib/utils";

interface JobCardProps {
  job: Job;
  match?: MatchResult;
  onMatchClick?: (job: Job) => void;
  onMatch?: (job: Job) => void;
  onSaveClick?: (job: Job) => void;
  onApply?: (job: Job) => void;
  onSkip?: (job: Job) => void;
  isSaving?: boolean;
}

function JobCard({
  job,
  match,
  onMatchClick,
  onMatch,
  onSaveClick,
  onApply,
  isSaving = false,
}: JobCardProps) {
  const matchScore = match?.score ?? job.match_score;
  const isRemote = job.remote ?? false;

  const handleMatch = () => {
    if (onMatchClick) onMatchClick(job);
    else if (onMatch) onMatch(job);
  };

  const cleanDescription = job.description ? stripHtml(job.description) : "";

  return (
    <div className="p-6 rounded-2xl bg-surface border border-border shadow-sm hover:shadow-md flex flex-col justify-between h-full group hover:border-primary/30 transition-all relative overflow-hidden">
      {/* Top Header: Company Avatar + Title + Match Badge */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-surface-elevated border border-border/50 flex items-center justify-center font-bold text-sm text-primary shadow-sm shrink-0 transition-transform group-hover:scale-105">
              {getInitials(job.company)}
            </div>

            <div>
              <h3 className="font-bold text-text text-base leading-tight group-hover:text-primary transition-colors line-clamp-1 mb-1">
                {job.title}
              </h3>
              <p className="text-sm text-text-secondary flex items-center gap-1.5 font-medium">
                <Building2 size={14} className="text-text-muted" />
                {job.company}
              </p>
            </div>
          </div>

          {matchScore !== undefined && matchScore !== null && (
            <MatchBadge score={matchScore} />
          )}
        </div>

        {/* Location & Tags */}
        <div className="flex flex-wrap items-center gap-2 mb-4 text-xs">
          <span className="flex items-center gap-1 font-medium text-text-secondary bg-surface-elevated px-2 py-1 rounded-md border border-border/50">
            <MapPin size={14} className="text-text-muted" />
            {job.location}
          </span>

          {isRemote && (
            <Badge variant="accent" className="text-xs px-2.5 py-1 font-medium">
              Remote
            </Badge>
          )}

          {job.salary && (
            <Badge variant="success" className="text-xs px-2.5 py-1 font-medium">
              {job.salary}
            </Badge>
          )}

          <Badge variant="default" className="text-xs px-2.5 py-1 capitalize text-text-muted">
            {job.source}
          </Badge>
        </div>

        {/* Short Description */}
        <p className="text-sm text-text-secondary line-clamp-3 leading-relaxed mb-6 flex-1">
          {cleanDescription}
        </p>
      </div>

      {/* Action Footer */}
      <div className="pt-4 flex flex-wrap items-center justify-between gap-3 mt-auto border-t border-border/50">
        <div className="flex flex-wrap items-center gap-2">
          {(onMatchClick || onMatch) && (
            <Button
              variant="secondary"
              size="sm"
              onClick={handleMatch}
              icon={<Sparkles size={16} className="text-accent" />}
              className="text-sm hover:text-accent font-medium bg-surface-elevated hover:bg-surface-elevated/80 border-transparent shadow-sm"
            >
              AI Fit
            </Button>
          )}

          {onApply && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onApply(job)}
              className="text-sm font-medium px-4 shadow-sm"
            >
              Apply
            </Button>
          )}
          
          {onSaveClick && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSaveClick(job)}
              isLoading={isSaving}
              icon={<Bookmark size={16} />}
              className="text-sm hover:text-primary p-2"
            >
              Save
            </Button>
          )}
        </div>

        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-text-muted hover:text-primary transition-colors p-2"
        >
          Details <ExternalLink size={14} />
        </a>
      </div>
    </div>
  );
}

export default JobCard;

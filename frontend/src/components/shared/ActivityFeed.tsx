import type { RecentActivityItem } from "../../types/dashboard";
import { formatRelativeDate } from "../../lib/utils";
import { Sparkles, Briefcase, FileCheck, CheckCircle2 } from "lucide-react";

interface ActivityFeedProps {
  activities: RecentActivityItem[];
}

function ActivityFeed({ activities }: ActivityFeedProps) {
  if (activities.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-text-muted">
        No recent activity logs yet.
      </div>
    );
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "job_discovered":
        return <Sparkles size={16} className="text-primary" />;
      case "application_submitted":
        return <FileCheck size={16} className="text-success" />;
      case "status_change":
        return <CheckCircle2 size={16} className="text-warning" />;
      default:
        return <Briefcase size={16} className="text-text-muted" />;
    }
  };

  return (
    <div className="space-y-4">
      {activities.map((item) => (
        <div
          key={item.id}
          className="flex items-start gap-4 p-4 rounded-xl bg-surface border border-transparent hover:bg-surface-elevated hover:border-border transition-colors group"
        >
          <div className="h-10 w-10 rounded-full bg-surface-elevated border border-border flex items-center justify-center shrink-0 mt-0.5 group-hover:scale-105 transition-transform shadow-sm">
            {getActivityIcon(item.type)}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-3 mb-1">
              <h5 className="text-sm font-semibold text-text truncate">
                {item.title}
              </h5>
              <span className="text-xs font-medium text-text-muted shrink-0 bg-surface-elevated px-2 py-0.5 rounded-md border border-border/50">
                {formatRelativeDate(item.timestamp)}
              </span>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed line-clamp-2">
              {item.description}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default ActivityFeed;

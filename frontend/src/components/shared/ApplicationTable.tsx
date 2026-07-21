/**
 * ApplicationTable Component
 *
 * Renders tracked job applications in a responsive table with status badges, match scores,
 * relative dates, and action menus for transitioning statuses.
 */

import type { Application } from "../../types/application";
import StatusBadge from "./StatusBadge";
import MatchBadge from "./MatchBadge";
import { Button, Select } from "../ui";
import { ExternalLink, Calendar, Building2, MapPin } from "lucide-react";
import { formatDate, getInitials } from "../../lib/utils";

interface ApplicationTableProps {
  applications: Application[];
  onSelectApplication: (app: Application) => void;
  onUpdateStatus: (id: string, newStatus: string) => void;
  onStartApply?: (app: Application) => void;
}

const STATUS_TRANSITION_OPTIONS = [
  { value: "saved", label: "Saved" },
  { value: "approved", label: "Approve for Apply" },
  { value: "completed", label: "Mark as Applied" },
  { value: "interview", label: "Interviewing" },
  { value: "offer", label: "Offer Received" },
  { value: "rejected", label: "Rejected" },
];

function ApplicationTable({
  applications,
  onSelectApplication,
  onUpdateStatus,
  onStartApply,
}: ApplicationTableProps) {
  return (
    <div className="w-full overflow-x-auto rounded-[16px] glass border border-border shadow-sm">
      <table className="w-full min-w-[800px] text-left text-sm text-text-secondary border-collapse">
        <thead className="bg-surface-elevated/80 text-text-muted font-semibold uppercase tracking-wider border-b border-border text-xs sticky top-0 z-10 backdrop-blur-md">
          <tr>
            <th className="py-4 px-6 font-semibold">Company & Position</th>
            <th className="py-4 px-6 font-semibold">Location</th>
            <th className="py-4 px-6 font-semibold">Match %</th>
            <th className="py-4 px-6 font-semibold">Status</th>
            <th className="py-4 px-6 font-semibold">Date Updated</th>
            <th className="py-4 px-6 text-right font-semibold">Actions</th>
          </tr>
        </thead>

        <tbody className="divide-y divide-border/40">
          {applications.map((app) => (
            <tr
              key={app.id}
              onClick={() => onSelectApplication(app)}
              className="hover:bg-surface-elevated/60 transition-colors cursor-pointer group"
            >
              {/* Company & Role */}
              <td className="py-4 px-6">
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-[12px] bg-surface-elevated border border-border flex items-center justify-center font-bold text-sm text-primary shrink-0 shadow-sm">
                    {getInitials(app.job.company)}
                  </div>
                  <div>
                    <h4 className="font-semibold text-text group-hover:text-primary transition-colors text-sm">
                      {app.job.title}
                    </h4>
                    <p className="text-text-muted flex items-center gap-1 text-[11px]">
                      <Building2 size={12} /> {app.job.company}
                    </p>
                  </div>
                </div>
              </td>

              {/* Location */}
              <td className="py-4 px-6">
                <span className="flex items-center gap-1.5 text-text-secondary">
                  <MapPin size={14} className="text-text-muted" />
                  {app.job.location}
                </span>
              </td>

              {/* Match Score */}
              <td className="py-4 px-6">
                {app.match_score !== undefined && app.match_score !== null ? (
                  <MatchBadge score={app.match_score} />
                ) : (
                  <span className="text-text-muted">—</span>
                )}
              </td>

              {/* Status */}
              <td className="py-4 px-6">
                <StatusBadge status={app.status} />
              </td>

              {/* Date */}
              <td className="py-4 px-6 text-text-muted">
                <span className="flex items-center gap-1.5 text-xs">
                  <Calendar size={14} />
                  {formatDate(app.updated_at)}
                </span>
              </td>

              {/* Action Buttons */}
              <td className="py-4 px-6 text-right" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-end gap-2">
                  {/* Quick Playwright Apply Button for Approved Roles */}
                  {app.status === "approved" && onStartApply && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => onStartApply(app)}
                    >
                      Start Apply
                    </Button>
                  )}

                  {/* Status Dropdown */}
                  <Select
                    value={app.status}
                    onChange={(e) => onUpdateStatus(app.id, e.target.value)}
                    options={STATUS_TRANSITION_OPTIONS}
                    className="text-xs py-1 px-2.5 h-8 bg-surface-elevated border-border"
                  />

                  {/* External Listing Link */}
                  <a
                    href={app.job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 rounded-lg text-text-muted hover:text-text hover:bg-surface-elevated transition-colors"
                  >
                    <ExternalLink size={14} />
                  </a>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ApplicationTable;

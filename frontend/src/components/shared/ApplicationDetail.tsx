/**
 * ApplicationDetail Component
 *
 * Slide-over/modal drawer displaying full application details:
 * - Associated job details and direct link
 * - Editable user notes (interview prep, contacts, referral info)
 * - Chronological audit log timeline of all status transitions
 */

import { useState, useEffect } from "react";
import type { Application } from "../../types/application";
import StatusBadge from "./StatusBadge";
import MatchBadge from "./MatchBadge";
import { Button } from "../ui";
import {
  Building2,
  MapPin,
  ExternalLink,
  Save,
  Clock,
  FileText,
  DollarSign,
  History,
} from "lucide-react";
import { formatDate } from "../../lib/utils";

interface ApplicationDetailProps {
  application: Application;
  onSaveNotes: (id: string, notes: string) => void;
  isSavingNotes?: boolean;
}

function ApplicationDetail({
  application,
  onSaveNotes,
  isSavingNotes = false,
}: ApplicationDetailProps) {
  const [notes, setNotes] = useState(application.notes || "");
  const [isNotesDirty, setIsNotesDirty] = useState(false);

  useEffect(() => {
    setNotes(application.notes || "");
    setIsNotesDirty(false);
  }, [application]);

  const handleNotesChange = (text: string) => {
    setNotes(text);
    setIsNotesDirty(true);
  };

  const handleSave = () => {
    onSaveNotes(application.id, notes);
    setIsNotesDirty(false);
  };

  return (
    <div className="space-y-8">
      {/* Header Info Banner */}
      <div className="p-6 glass rounded-[20px] flex items-start justify-between gap-6 shadow-sm">
        <div>
          <h3 className="text-xl font-bold text-text mb-2">
            {application.job.title}
          </h3>
          <div className="flex flex-wrap items-center gap-4 text-sm text-text-secondary">
            <span className="font-semibold text-primary flex items-center gap-1.5">
              <Building2 size={16} /> {application.job.company}
            </span>
            <span className="flex items-center gap-1.5">
              <MapPin size={16} className="text-text-muted" /> {application.job.location}
            </span>
            {application.job.salary && (
              <span className="flex items-center gap-1.5 text-success font-medium">
                <DollarSign size={16} /> {application.job.salary}
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-3 shrink-0">
          <StatusBadge status={application.status} />
          {application.match_score !== undefined && application.match_score !== null && (
            <MatchBadge score={application.match_score} />
          )}
        </div>
      </div>

      {/* Editable Notes Section */}
      <div className="p-6 glass rounded-[20px] border border-border shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-bold text-text uppercase tracking-wider flex items-center gap-2">
            <FileText size={16} className="text-primary" /> Application Notes
          </h4>

          {isNotesDirty && (
            <Button
              variant="primary"
              size="sm"
              isLoading={isSavingNotes}
              onClick={handleSave}
              icon={<Save size={14} />}
            >
              Save Notes
            </Button>
          )}
        </div>

        <textarea
          value={notes}
          onChange={(e) => handleNotesChange(e.target.value)}
          placeholder="Add notes about your application, recruiter contacts, or interview preparation..."
          rows={5}
          className="w-full bg-surface/60 border border-border rounded-[12px] p-4 text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
        />
      </div>

      {/* Audit Log History Timeline */}
      <div className="px-2">
        <h4 className="text-sm font-bold text-text uppercase tracking-wider mb-4 flex items-center gap-2">
          <History size={16} className="text-accent" /> Status History & Audit Log
        </h4>

        {application.logs.length === 0 ? (
          <div className="text-xs text-text-muted">No audit logs recorded yet.</div>
        ) : (
          <div className="space-y-2.5">
            {application.logs.map((log) => (
              <div
                key={log.id}
                className="p-3 rounded-[12px] bg-surface-elevated/40 border border-border text-xs flex items-start gap-3"
              >
                <div className="h-7 w-7 rounded-full bg-surface-elevated border border-border flex items-center justify-center shrink-0 mt-0.5 text-text-muted">
                  <Clock size={14} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-text">{log.action}</span>
                    <span className="text-[10px] text-text-muted">
                      {formatDate(log.created_at)}
                    </span>
                  </div>
                  {log.details && (
                    <p className="text-xs text-text-secondary mt-0.5">{log.details}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* External Direct Link */}
      <div className="pt-2 flex justify-end">
        <a
          href={application.job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-primary font-semibold hover:underline"
        >
          Open Original Job Listing Page <ExternalLink size={14} />
        </a>
      </div>
    </div>
  );
}

export default ApplicationDetail;

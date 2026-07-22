/**
 * ResumeCard Component
 *
 * Renders an uploaded resume record with filename, date, active badge, and action buttons.
 */

import type { Resume } from "../../types/resume";
import { Card, Badge, Button } from "../ui";
import { FileText, CheckCircle, Calendar, Sparkles, Trash2 } from "lucide-react";
import { formatDate } from "../../lib/utils";

interface ResumeCardProps {
  resume: Resume;
  onSetActive?: (resumeId: string) => void;
  onParse?: (resumeId: string) => void;
  onDelete?: (resume: Resume) => void;
  isSettingActive?: boolean;
  isDeleting?: boolean;
}

function ResumeCard({
  resume,
  onSetActive,
  onParse,
  onDelete,
  isSettingActive,
  isDeleting,
}: ResumeCardProps) {
  return (
    <Card hoverable className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 shadow-sm">
      <div className="flex items-center gap-4 min-w-0">
        <div className="h-12 w-12 rounded-[16px] bg-primary/10 text-primary border border-primary/20 flex items-center justify-center shrink-0">
          <FileText size={24} />
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-text truncate">
              {resume.filename}
            </h4>
            {resume.is_active && (
              <Badge variant="success" className="text-[10px] shrink-0">
                <CheckCircle size={10} className="mr-1 inline" />
                Active
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs text-text-muted mt-0.5">
            <span className="flex items-center gap-1">
              <Calendar size={12} />
              Uploaded {formatDate(resume.uploaded_at)}
            </span>

            {resume.parsed_data && (
              <span className="text-primary font-medium flex items-center gap-1">
                <Sparkles size={12} /> Parsed
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto">
        {onParse && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onParse(resume.id)}
            icon={<Sparkles size={14} />}
          >
            {resume.parsed_data ? "View Parsed" : "Parse Skills"}
          </Button>
        )}

        {!resume.is_active && onSetActive && (
          <Button
            variant="ghost"
            size="sm"
            isLoading={isSettingActive}
            onClick={() => onSetActive(resume.id)}
          >
            Make Active
          </Button>
        )}

        {onDelete && (
          <Button
            variant="danger"
            size="sm"
            isLoading={isDeleting}
            onClick={() => onDelete(resume)}
            title="Delete Resume"
            icon={<Trash2 size={14} />}
          />
        )}
      </div>
    </Card>
  );
}

export default ResumeCard;


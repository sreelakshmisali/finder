/**
 * ParsedResumeView Component
 *
 * Renders structured resume fields extracted by AI:
 * Contact info, skill badges, experience timeline, and education records.
 */

import type { ParsedResumeData } from "../../types/resume";
import { Badge } from "../ui";
import { User, Mail, Phone, Wrench, Briefcase, GraduationCap } from "lucide-react";

interface ParsedResumeViewProps {
  data?: ParsedResumeData | Record<string, unknown> | null;
}

function ParsedResumeView({ data }: ParsedResumeViewProps) {
  if (!data) {
    return (
      <div className="py-8 text-center text-xs text-text-muted">
        No parsed data available yet. Click "Parse Skills" to extract structured resume data.
      </div>
    );
  }

  const parsed = data as ParsedResumeData;
  const skills = parsed.skills || [];
  const experience = parsed.experience || [];
  const education = parsed.education || [];

  return (
    <div className="space-y-8">
      {/* Contact Header */}
      <div className="p-6 glass rounded-[20px] flex flex-wrap items-center justify-between gap-4 shadow-sm">
        {parsed.full_name && (
          <div className="flex items-center gap-2 font-bold text-text text-lg">
            <User size={20} className="text-primary" />
            {parsed.full_name}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-6 text-sm text-text-secondary font-medium">
          {parsed.email && (
            <span className="flex items-center gap-1.5">
              <Mail size={16} className="text-text-muted" />
              {parsed.email}
            </span>
          )}

          {parsed.phone && (
            <span className="flex items-center gap-1.5">
              <Phone size={16} className="text-text-muted" />
              {parsed.phone}
            </span>
          )}
        </div>
      </div>

      {/* Extracted Skills Badges */}
      {skills.length > 0 && (
        <div className="px-2">
          <h4 className="text-sm font-bold text-text uppercase tracking-wider mb-4 flex items-center gap-2">
            <Wrench size={16} className="text-primary" /> Extracted Skills ({skills.length})
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {skills.map((skill, i) => (
              <Badge key={i} variant="primary" className="px-2.5 py-1 text-xs">
                {String(skill)}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Experience Entries */}
      {experience.length > 0 && (
        <div className="px-2">
          <h4 className="text-sm font-bold text-text uppercase tracking-wider mb-4 flex items-center gap-2">
            <Briefcase size={16} className="text-accent" /> Work Experience
          </h4>
          <div className="space-y-4">
            {experience.map((item, i) => (
              <div key={i} className="p-4 rounded-[16px] bg-surface-elevated/50 border border-border shadow-sm">
                <div className="flex items-center justify-between">
                  <h5 className="text-base font-semibold text-text">
                    {String(item.title || "Role Title")}
                  </h5>
                  <span className="text-[11px] text-text-muted">
                    {String(item.duration || "")}
                  </span>
                </div>
                <p className="text-xs text-primary font-medium mt-0.5">
                  {String(item.company || "")}
                </p>
                {item.description ? (
                  <p className="text-xs text-text-secondary mt-1 line-clamp-2">
                    {String(item.description)}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Education Entries */}
      {education.length > 0 && (
        <div className="px-2">
          <h4 className="text-sm font-bold text-text uppercase tracking-wider mb-4 flex items-center gap-2">
            <GraduationCap size={16} className="text-success" /> Education
          </h4>
          <div className="space-y-3">
            {education.map((item, i) => (
              <div key={i} className="p-4 rounded-[16px] bg-surface-elevated/50 border border-border shadow-sm flex items-center justify-between">
                <div>
                  <h5 className="text-base font-semibold text-text">
                    {String(item.degree || "Degree")}
                  </h5>
                  <p className="text-xs text-text-secondary">
                    {String(item.institution || "")}
                  </p>
                </div>
                <span className="text-[11px] text-text-muted">
                  {String(item.year || "")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ParsedResumeView;

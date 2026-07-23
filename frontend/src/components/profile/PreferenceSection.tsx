/**
 * PreferenceSection Component
 *
 * Section 2 of Profile Setup Page:
 * Form for setting candidate goals: target roles, locations, salary range, work mode,
 * target companies, and experience level. Optional and skippable.
 */

import { useState, useEffect } from "react";
import TagInput from "../shared/TagInput";
import { Card, CardHeader, CardTitle, Button, Input, Spinner, Badge } from "../ui";
import { usePreferences, useSavePreferences } from "../../hooks/usePreferences";
import type { PreferenceUpdatePayload } from "../../types/preference";
import type { Preference } from "../../types/preference";
import {
  Briefcase,
  DollarSign,
  Building,
  Save,
  CheckCircle2,
  Clock,
  Info,
} from "lucide-react";

interface PreferenceSectionProps {
  initialPreferences?: Preference | null;
}

export default function PreferenceSection({ initialPreferences }: PreferenceSectionProps) {
  const { data: prefData, isLoading, isError } = usePreferences();
  const saveMutation = useSavePreferences();

  const [roles, setRoles] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [minSalary, setMinSalary] = useState<number>(100000);
  const [maxSalary, setMaxSalary] = useState<number>(180000);
  const [workType, setWorkType] = useState<string>("remote");
  const [companies, setCompanies] = useState<string[]>([]);
  const [experienceYears, setExperienceYears] = useState<number>(3);
  const [showSavedToast, setShowSavedToast] = useState(false);

  // Sync state when preferences finish loading or initialPreferences provided
  useEffect(() => {
    const target = prefData || initialPreferences;
    if (target) {
      setRoles(target.preferred_roles || []);
      setLocations(target.preferred_locations || []);
      setMinSalary(target.min_salary || 100000);
      setMaxSalary(target.max_salary || 180000);
      setWorkType(target.work_type || "remote");
      setCompanies(target.preferred_companies || []);
      setExperienceYears(target.experience_years || 3);
    }
  }, [prefData, initialPreferences]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: PreferenceUpdatePayload = {
      preferred_roles: roles,
      preferred_locations: locations,
      min_salary: minSalary,
      max_salary: maxSalary,
      work_type: workType,
      preferred_companies: companies,
      experience_years: experienceYears,
    };

    saveMutation.mutate(payload, {
      onSuccess: () => {
        setShowSavedToast(true);
        setTimeout(() => setShowSavedToast(false), 4000);
      },
    });
  };

  return (
    <div id="preferences-section" className="space-y-6 scroll-mt-6">
      {/* Section Header */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-xl font-black text-text tracking-tight">
              2. Job Preferences & Target Goals
            </h3>
            <Badge variant="default" className="text-xs px-2.5 py-0.5 font-bold uppercase bg-surface-elevated">
              Optional
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Specify target roles, preferred locations, salary expectations, and dream companies.
          </p>
        </div>

        <Button
          type="button"
          variant="primary"
          onClick={handleSubmit}
          isLoading={saveMutation.isPending}
          icon={<Save size={16} />}
          className="hidden sm:flex text-xs font-semibold shadow-sm"
        >
          Save Preferences
        </Button>
      </div>

      {/* Optional Banner Info Notice */}
      <div className="p-4 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-between gap-3 text-xs text-primary font-medium">
        <div className="flex items-center gap-2">
          <Info size={16} className="shrink-0" />
          <span>Preferences are optional and enrich AI job matching rankings. You can skip this section at any time.</span>
        </div>
      </div>

      {/* Loading Spinner */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <Spinner size="md" />
        </div>
      )}

      {/* Error Notice */}
      {isError && (
        <div className="p-4 text-xs rounded-xl bg-error/15 border border-error/30 text-error font-medium">
          Failed to load preferences. Check backend connection.
        </div>
      )}

      {/* Saved Success Toast Notification */}
      {showSavedToast && (
        <div className="p-4 rounded-xl bg-success/15 border border-success/40 text-success text-xs font-semibold flex items-center gap-2 animate-in fade-in duration-200">
          <CheckCircle2 size={18} />
          Your job search preferences have been saved successfully!
        </div>
      )}

      {!isLoading && (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Target Roles & Locations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase size={18} className="text-primary" />
                Target Roles & Locations
              </CardTitle>
            </CardHeader>

            <div className="space-y-6">
              <TagInput
                label="Preferred Job Titles"
                tags={roles}
                onChange={setRoles}
                placeholder="e.g. Senior Backend Engineer, Python Architect (press Enter)"
                variant="primary"
              />

              <TagInput
                label="Preferred Locations"
                tags={locations}
                onChange={setLocations}
                placeholder="e.g. Remote, San Francisco CA, New York NY (press Enter)"
                variant="default"
              />
            </div>
          </Card>

          {/* Compensation & Work Arrangement */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign size={18} className="text-success" />
                Salary Range & Work Arrangement
              </CardTitle>
            </CardHeader>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
              <Input
                type="number"
                label="Minimum Annual Salary (USD)"
                value={minSalary}
                onChange={(e) => setMinSalary(Number(e.target.value))}
                step={5000}
              />

              <Input
                type="number"
                label="Target Maximum Salary (USD)"
                value={maxSalary}
                onChange={(e) => setMaxSalary(Number(e.target.value))}
                step={5000}
              />
            </div>

            {/* Work Type Selection Pills */}
            <div>
              <label className="text-xs font-semibold text-text mb-2.5 block">
                Work Arrangement Preference
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { id: "remote", label: "Remote Only", desc: "Work from anywhere" },
                  { id: "hybrid", label: "Hybrid", desc: "Flexible office & home" },
                  { id: "onsite", label: "On-site", desc: "Full time in office" },
                ].map((type) => {
                  const isSelected = workType === type.id;
                  return (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => setWorkType(type.id)}
                      className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                        isSelected
                          ? "bg-primary-muted/20 text-primary border-primary font-semibold shadow-sm"
                          : "bg-surface-elevated/40 border-border text-text-secondary hover:text-text hover:bg-surface-elevated"
                      }`}
                    >
                      <div className="text-xs font-bold mb-0.5">{type.label}</div>
                      <div className="text-[11px] text-text-muted">{type.desc}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </Card>

          {/* Preferred Companies & Experience */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building size={18} className="text-accent" />
                Target Companies & Experience Level
              </CardTitle>
            </CardHeader>

            <div className="space-y-6">
              <TagInput
                label="Target Preferred Companies"
                tags={companies}
                onChange={setCompanies}
                placeholder="e.g. Stripe, Notion, Figma, OpenAI (press Enter)"
                variant="accent"
              />

              <div className="w-full md:w-64">
                <Input
                  type="number"
                  label="Years of Experience"
                  value={experienceYears}
                  onChange={(e) => setExperienceYears(Number(e.target.value))}
                  min={0}
                  max={40}
                  icon={<Clock size={16} />}
                />
              </div>
            </div>
          </Card>

          {/* Save Action Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t border-border/50">
            <span className="text-xs text-text-muted">
              Saving preferences updates your matching rankings automatically.
            </span>

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={saveMutation.isPending}
              icon={<Save size={16} />}
              className="w-full sm:w-auto text-xs font-bold px-6 shadow-md shadow-primary/20"
            >
              Save Preferences
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}

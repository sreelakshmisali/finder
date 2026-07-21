/**
 * Preferences Page Component
 *
 * Full job preference management interface:
 * - Preferred roles tag input
 * - Preferred locations tag input
 * - Minimum & target maximum salary inputs
 * - Work type toggle pills (Remote, Hybrid, On-site)
 * - Preferred companies tag input
 * - Years of experience level input
 */

import { useState, useEffect } from "react";
import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import TagInput from "../components/shared/TagInput";
import { Card, CardHeader, CardTitle, Button, Input, Spinner } from "../components/ui";
import { usePreferences, useSavePreferences } from "../hooks/usePreferences";
import type { PreferenceUpdatePayload } from "../types/preference";
import {
  Briefcase,
  DollarSign,
  Building,
  Save,
  CheckCircle2,
  Clock,
} from "lucide-react";

function PreferencesPage() {
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

  // Sync state when preferences data finishes loading
  useEffect(() => {
    if (prefData) {
      setRoles(prefData.preferred_roles || []);
      setLocations(prefData.preferred_locations || []);
      setMinSalary(prefData.min_salary || 100000);
      setMaxSalary(prefData.max_salary || 180000);
      setWorkType(prefData.work_type || "remote");
      setCompanies(prefData.preferred_companies || []);
      setExperienceYears(prefData.experience_years || 3);
    }
  }, [prefData]);

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
    <>
      <Header
        title="Job Preferences"
        subtitle="Configure criteria used by the AI matching service to rank target roles"
        actions={
          <Button
            type="button"
            variant="primary"
            onClick={handleSubmit}
            isLoading={saveMutation.isPending}
            icon={<Save size={16} />}
          >
            Save Preferences
          </Button>
        }
      />

      <PageWrapper>
        {/* Loading Spinner */}
        {isLoading && (
          <div className="flex justify-center py-24">
            <Spinner size="lg" />
          </div>
        )}

        {/* Error Notice */}
        {isError && (
          <div className="mb-6 p-4 glass border border-error/30 rounded-[12px] text-error text-sm">
            Failed to load preferences. Check backend connection.
          </div>
        )}

        {/* Saved Success Toast Notification */}
        {showSavedToast && (
          <div className="mb-6 p-4 glass border border-success/40 bg-success-muted/20 rounded-[12px] flex items-center gap-3 text-success text-sm font-medium animate-fadeIn">
            <CheckCircle2 size={20} />
            Your job search preferences have been saved successfully!
          </div>
        )}

        {!isLoading && (
          <form onSubmit={handleSubmit} className="space-y-6 max-w-3xl mx-auto w-full">
            {/* Preferred Roles & Locations */}
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
                <label className="text-sm font-semibold text-text mb-3 block">
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
                        className={`p-3 sm:p-4 rounded-[12px] border text-left transition-all cursor-pointer ${
                          isSelected
                            ? "bg-primary-muted text-primary border-primary font-semibold shadow-sm"
                            : "bg-surface-elevated/40 border-border text-text-secondary hover:text-text hover:bg-surface-elevated"
                        }`}
                      >
                        <div className="text-sm font-semibold mb-0.5">{type.label}</div>
                        <div className="text-xs text-text-muted">{type.desc}</div>
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

            {/* Bottom Save Action Button */}
            <div className="flex justify-end pt-4">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                isLoading={saveMutation.isPending}
                icon={<Save size={18} />}
                className="w-full sm:w-auto"
              >
                Save All Preferences
              </Button>
            </div>
          </form>
        )}
      </PageWrapper>
    </>
  );
}

export default PreferencesPage;

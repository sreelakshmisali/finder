/**
 * Preference TypeScript Type Definitions
 */

export interface Preference {
  id?: string;
  preferred_roles: string[];
  preferred_locations: string[];
  min_salary: number;
  max_salary: number;
  work_type: "remote" | "hybrid" | "onsite" | string;
  preferred_companies: string[];
  experience_years: number;
  updated_at?: string;
}

export type PreferenceUpdatePayload = Omit<Preference, "id" | "updated_at">;

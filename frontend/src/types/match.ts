/**
 * Match TypeScript Type Definitions
 */

export interface MatchRequest {
  job_id: string;
  resume_id?: string;
}

export interface BatchMatchRequest {
  job_ids: string[];
  resume_id?: string;
}

export interface MatchResult {
  job_id: string;
  score: number;
  resume_match: number;
  preference_match: number;
  missing_skills: string[];
  reason?: string;
  reasons: string[];
  recommendation?: string;
  score_breakdown?: {
    resume_compatibility_raw?: number;
    preference_alignment_raw?: number;
    skills_match?: number;
    experience_match?: number;
    role_similarity?: number;
    tech_overlap?: number;
    location_match?: number;
    salary_match?: number;
    remote_match?: number;
    company_match?: number;
    keyword_score?: number;
    preference_bonus?: number;
  };
}

export interface BatchMatchResult {
  matches: MatchResult[];
}

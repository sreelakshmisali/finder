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
  missing_skills: string[];
  reason?: string;
  reasons: string[];
  recommendation?: string;
  score_breakdown?: {
    resume_compatibility_raw?: number;
    skills_match?: number;
    experience_match?: number;
    role_similarity?: number;
    tech_overlap?: number;
    keyword_score?: number;
  };
}

export interface BatchMatchResult {
  matches: MatchResult[];
}

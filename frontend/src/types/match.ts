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
  reasons: string[];
  missing_skills: string[];
  recommendation: string;
  score_breakdown?: {
    keyword_score: number;
    preference_bonus: number;
  };
}

export interface BatchMatchResult {
  matches: MatchResult[];
}

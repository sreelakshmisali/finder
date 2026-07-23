/**
 * Dashboard TypeScript Type Definitions
 */

import type { Job } from "./job";

export interface RecentActivityItem {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  type: string;
}

export interface DashboardStats {
  total_jobs_found: number;
  high_matches_count?: number;
  saved_jobs_count: number;
  applied_count: number;
  interviews_count: number;
  offers_count: number;
  recent_jobs: Job[];
  recent_activities: RecentActivityItem[];
}

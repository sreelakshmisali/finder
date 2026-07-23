/**
 * Notification TypeScript Type Definitions
 */

import type { Job } from "./job";

export interface Notification {
  id: string;
  user_id: string;
  job_id?: string | null;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  job?: Job | null;
}

export interface NotificationUnreadCount {
  unread_count: number;
}

export interface PipelineRunResult {
  user_id: string;
  saved_searches_processed: number;
  jobs_evaluated: number;
  new_notifications_created: number;
  message: string;
}

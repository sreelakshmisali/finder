/**
 * Saved Search TypeScript Type Definitions
 */

import type { SearchMode } from "./job";

export interface SavedSearch {
  id: string;
  user_id: string;
  name: string;
  query?: string | null;
  filters: Record<string, any>;
  mode: SearchMode;
  created_at: string;
  last_run?: string | null;
}

export interface SavedSearchCreate {
  name: string;
  query?: string;
  filters?: Record<string, any>;
  mode: SearchMode;
}

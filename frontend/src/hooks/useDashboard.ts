/**
 * React Query Hook for Dashboard Operations
 */

import { useQuery } from "@tanstack/react-query";
import { fetchDashboardStats } from "../services/dashboardService";

/**
 * Custom hook to fetch dashboard summary stats.
 */
export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: fetchDashboardStats,
    staleTime: 1000 * 60 * 2, // Cache stats for 2 minutes
  });
}

/**
 * React Query Hook for Onboarding Status
 */

import { useQuery } from "@tanstack/react-query";
import { fetchOnboardingStatus } from "../services/onboardingService";
import { useAuth } from "../contexts/AuthContext";

/**
 * Custom hook to fetch candidate onboarding status metrics.
 * Safely guards execution until authentication token is loaded.
 */
export function useOnboardingStatus() {
  const { token, isLoading: isAuthLoading } = useAuth();

  return useQuery({
    queryKey: ["onboarding", "status"],
    queryFn: fetchOnboardingStatus,
    enabled: Boolean(token) && !isAuthLoading,
    staleTime: 1000 * 30, // 30 seconds
  });
}

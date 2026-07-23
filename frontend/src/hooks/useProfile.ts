/**
 * React Query Hook for Profile Setup Operations
 */

import { useQuery } from "@tanstack/react-query";
import { fetchProfileSetup } from "../services/profileService";
import { useAuth } from "../contexts/AuthContext";

/**
 * Custom hook to fetch combined candidate profile setup details.
 * Safely guards call until authentication token is active.
 */
export function useProfileSetup() {
  const { token, isLoading: isAuthLoading } = useAuth();

  return useQuery({
    queryKey: ["profile", "setup"],
    queryFn: fetchProfileSetup,
    enabled: Boolean(token) && !isAuthLoading,
    staleTime: 1000 * 30, // 30 seconds
  });
}

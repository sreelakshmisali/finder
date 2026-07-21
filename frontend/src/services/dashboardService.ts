/**
 * Dashboard Service API Client
 *
 * Calls `/dashboard/stats` endpoint.
 */

import api from "./api";
import type { DashboardStats } from "../types/dashboard";

/**
 * Fetch summary stats for the dashboard.
 */
export async function fetchDashboardStats(): Promise<DashboardStats> {
  const response = await api.get<DashboardStats>("/dashboard/stats");
  return response.data;
}

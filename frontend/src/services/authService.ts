/**
 * Auth Service API Client
 *
 * Calls `/auth` endpoints.
 */

import api from "./api";
import type { TokenResponse, User } from "../types/auth";

/**
 * Register a new user account.
 */
export async function register(payload: Record<string, string>): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>("/auth/register", payload);
  return response.data;
}

/**
 * Log in with email and password.
 */
export async function login(payload: Record<string, string>): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>("/auth/login", payload);
  return response.data;
}

/**
 * Fetch current authenticated user profile.
 */
export async function fetchCurrentUser(): Promise<User> {
  const response = await api.get<User>("/auth/me");
  return response.data;
}

/**
 * Auth Context Provider
 *
 * Manages global authentication state, token persistence in localStorage,
 * and sets Bearer Authorization headers on the Axios API instance.
 */

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import type { User, TokenResponse } from "../types/auth";
import { register as apiRegister, login as apiLogin, fetchCurrentUser } from "../services/authService";
import api from "../services/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, fullName: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("finder_token"));
  const [isLoading, setIsLoading] = useState(true);

  // Sync token to Axios headers and load user profile
  useEffect(() => {
    if (token) {
      localStorage.setItem("finder_token", token);
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`;

      fetchCurrentUser()
        .then((u) => setUser(u))
        .catch(() => {
          // If token is invalid or expired, clear auth state
          logout();
        })
        .finally(() => setIsLoading(false));
    } else {
      localStorage.removeItem("finder_token");
      delete api.defaults.headers.common["Authorization"];
      setUser(null);
      setIsLoading(false);
    }
  }, [token]);

  const handleAuthSuccess = (res: TokenResponse) => {
    setToken(res.access_token);
    setUser(res.user);
  };

  const login = async (email: string, password: string) => {
    const res = await apiLogin({ email, password });
    handleAuthSuccess(res);
  };

  const register = async (email: string, fullName: string, password: string) => {
    const res = await apiRegister({ email, full_name: fullName, password });
    handleAuthSuccess(res);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("finder_token");
    delete api.defaults.headers.common["Authorization"];
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: Boolean(user),
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

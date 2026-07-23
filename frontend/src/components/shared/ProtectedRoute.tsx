/**
 * ProtectedRoute Guard Component
 *
 * Protects application routes from unauthenticated access.
 * Shows a sleek loading screen during token validation to prevent UI flicker,
 * and immediately redirects unauthenticated users to the `/login` page.
 */

import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { Loader2 } from "lucide-react";

export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // 1. Show centered loading spinner while checking initial token state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg flex flex-col justify-center items-center gap-3">
        <Loader2 size={28} className="animate-spin text-primary" />
        <span className="text-xs font-medium text-text-muted tracking-wide">
          Verifying session...
        </span>
      </div>
    );
  }

  // 2. If unauthenticated, redirect to /login and preserve requested path
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 3. Authenticated: Render protected nested layout
  return <Outlet />;
}

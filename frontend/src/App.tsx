/**
 * App Component
 *
 * Configures React Router routes, ProtectedRoute authentication guard,
 * React Query QueryClientProvider, and AuthProvider context.
 */

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/shared/ProtectedRoute";
import DashboardLayout from "./layouts/DashboardLayout";
import AuthPage from "./pages/AuthPage";
import JobsPage from "./pages/JobsPage";
import ProfilePage from "./pages/ProfilePage";

/* Create a single React Query client instance */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Authentication Entry Point */}
            <Route path="/login" element={<AuthPage />} />

            {/* Protected Application Routes (Requires Authentication Guard) */}
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<DashboardLayout />}>
                <Route index element={<Navigate to="/jobs" replace />} />
                <Route path="jobs" element={<JobsPage />} />
                <Route path="dashboard" element={<Navigate to="/jobs" replace />} />
                <Route path="profile" element={<ProfilePage />} />
                <Route path="resume" element={<Navigate to="/jobs" replace />} />
                <Route path="tracker" element={<Navigate to="/jobs" replace />} />
              </Route>
            </Route>

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/jobs" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;

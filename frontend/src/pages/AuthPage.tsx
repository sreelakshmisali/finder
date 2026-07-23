/**
 * AuthPage Component
 *
 * Dedicated full-page authentication screen for signing in or creating an account.
 * Replaces dismissible modals to ensure Finder remains a fully protected SaaS application.
 */

import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Input, Button } from "../components/ui";
import { Mail, Lock, User, LogIn, UserPlus, AlertCircle, Sparkles } from "lucide-react";

type AuthMode = "login" | "register";

export default function AuthPage() {
  const { login, register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // If user is already authenticated, redirect to target page or dashboard
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || "/";
  if (isAuthenticated) {
    navigate(from, { replace: true });
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsLoading(true);

    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, fullName, password);
      }
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const defaultErr = mode === "login" 
        ? "Invalid email or password. Please try again." 
        : "Failed to create account. Email may already be registered.";
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || defaultErr;
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex flex-col justify-center items-center p-4 relative selection:bg-primary-muted selection:text-white overflow-hidden">
      {/* Subtle SaaS Background Accent Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Main Container */}
      <div className="w-full max-w-[420px] relative z-10 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-primary text-white font-extrabold text-2xl shadow-lg shadow-primary/25 mb-1">
            F
          </div>
          <h1 className="text-2xl font-black tracking-tight text-text">
            Finder
          </h1>
          <p className="text-sm text-text-muted flex items-center justify-center gap-1.5 font-medium">
            <Sparkles size={14} className="text-primary" />
            AI-Powered Job Application Assistant
          </p>
        </div>

        {/* Auth Card */}
        <div className="bg-surface border border-border rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6 backdrop-blur-xl">
          {/* Segmented Control / Mode Switcher */}
          <div className="grid grid-cols-2 p-1 bg-surface-elevated/60 border border-border/50 rounded-xl text-sm font-medium">
            <button
              type="button"
              onClick={() => {
                setMode("login");
                setErrorMsg(null);
              }}
              className={`py-2 rounded-lg transition-all text-center cursor-pointer ${
                mode === "login"
                  ? "bg-surface text-text font-semibold shadow-sm border border-border/50"
                  : "text-text-muted hover:text-text"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("register");
                setErrorMsg(null);
              }}
              className={`py-2 rounded-lg transition-all text-center cursor-pointer ${
                mode === "register"
                  ? "bg-surface text-text font-semibold shadow-sm border border-border/50"
                  : "text-text-muted hover:text-text"
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Error Message Alert */}
          {errorMsg && (
            <div className="p-3.5 bg-error/15 border border-error/30 rounded-xl flex items-start gap-2.5 text-xs text-error animate-in fade-in duration-200">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <Input
                type="text"
                label="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
                icon={<User size={16} />}
                required
              />
            )}

            <Input
              type="email"
              label="Email Address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              icon={<Mail size={16} />}
              required
            />

            <Input
              type="password"
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === "register" ? "At least 6 characters" : "••••••••"}
              icon={<Lock size={16} />}
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full h-11 text-sm font-semibold mt-2 shadow-lg shadow-primary/20"
              isLoading={isLoading}
              icon={mode === "login" ? <LogIn size={16} /> : <UserPlus size={16} />}
            >
              {mode === "login" ? "Sign In to Account" : "Create Account"}
            </Button>
          </form>
        </div>

        {/* Footer Note */}
        <p className="text-center text-xs text-text-muted">
          Protected by Finder Authentication Guard. Standard SSL Encrypted.
        </p>
      </div>
    </div>
  );
}

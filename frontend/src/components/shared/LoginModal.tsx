/**
 * LoginModal Component
 *
 * User authentication modal for signing in with email and password.
 */

import { useState } from "react";
import { Modal, Input, Button } from "../ui";
import { useAuth } from "../../contexts/AuthContext";
import { LogIn, Mail, Lock, AlertCircle } from "lucide-react";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToRegister: () => void;
}

function LoginModal({ isOpen, onClose, onSwitchToRegister }: LoginModalProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsLoading(true);

    try {
      await login(email, password);
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Login failed. Check your credentials.";
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Sign In to Finder" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        {errorMsg && (
          <div className="p-3 bg-error/15 border border-error/30 rounded-[10px] flex items-center gap-2 text-xs text-error">
            <AlertCircle size={14} />
            <span>{errorMsg}</span>
          </div>
        )}

        <Input
          type="email"
          label="Email Address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="your.email@example.com"
          icon={<Mail size={16} />}
          required
        />

        <Input
          type="password"
          label="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          icon={<Lock size={16} />}
          required
        />

        <Button
          type="submit"
          variant="primary"
          size="md"
          className="w-full mt-2"
          isLoading={isLoading}
          icon={<LogIn size={16} />}
        >
          Sign In
        </Button>

        <div className="text-center text-sm text-text-muted pt-4 border-t border-border mt-4">
          Don't have an account?{" "}
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="text-primary font-semibold hover:text-primary-hover hover:underline cursor-pointer transition-colors"
          >
            Create Account
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default LoginModal;

/**
 * RegisterModal Component
 *
 * User registration modal for creating a new account.
 */

import { useState } from "react";
import { Modal, Input, Button } from "../ui";
import { useAuth } from "../../contexts/AuthContext";
import { UserPlus, Mail, Lock, User, AlertCircle } from "lucide-react";

interface RegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToLogin: () => void;
}

function RegisterModal({ isOpen, onClose, onSwitchToLogin }: RegisterModalProps) {
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsLoading(true);

    try {
      await register(email, fullName, password);
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Registration failed. Try another email.";
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Finder Account" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        {errorMsg && (
          <div className="p-3 bg-error/15 border border-error/30 rounded-[10px] flex items-center gap-2 text-xs text-error">
            <AlertCircle size={14} />
            <span>{errorMsg}</span>
          </div>
        )}

        <Input
          type="text"
          label="Full Name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Jane Doe"
          icon={<User size={16} />}
          required
        />

        <Input
          type="email"
          label="Email Address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="jane.doe@example.com"
          icon={<Mail size={16} />}
          required
        />

        <Input
          type="password"
          label="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 6 characters"
          icon={<Lock size={16} />}
          required
        />

        <Button
          type="submit"
          variant="primary"
          size="md"
          className="w-full mt-2"
          isLoading={isLoading}
          icon={<UserPlus size={16} />}
        >
          Register Account
        </Button>

        <div className="text-center text-sm text-text-muted pt-4 border-t border-border mt-4">
          Already have an account?{" "}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-primary font-semibold hover:text-primary-hover hover:underline cursor-pointer transition-colors"
          >
            Sign In
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default RegisterModal;

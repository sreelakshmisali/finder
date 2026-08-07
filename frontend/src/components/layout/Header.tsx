import type { ReactNode } from "react";
import { LogOut, User, Search } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { Button } from "../ui";

interface HeaderProps {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
}

function Header({ title, subtitle, actions }: HeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className="py-4 md:py-5 px-6 md:px-10 lg:px-12 border-b border-border/40 bg-surface/30 backdrop-blur-xl sticky top-0 z-20">
      <div className="w-full max-w-[1400px] mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-white shadow-md font-extrabold text-lg">
            <Search size={20} />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-extrabold tracking-tight text-text flex items-center gap-2">
              <span className="gradient-text-primary">{title || "Finder"}</span>
            </h1>
            {subtitle && (
              <p className="text-xs text-text-secondary font-medium hidden sm:block">{subtitle}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {user && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-elevated/60 border border-border text-xs font-semibold text-text-secondary">
              <User size={14} className="text-primary" />
              <span>{user.email}</span>
            </div>
          )}

          {actions}

          {logout && (
            <Button
              variant="secondary"
              size="sm"
              onClick={logout}
              icon={<LogOut size={14} />}
              title="Log Out"
            >
              Log Out
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;

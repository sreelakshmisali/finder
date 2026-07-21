/**
 * Header Component
 *
 * Top page header displaying title, subtitle, and right actions.
 */

import type { ReactNode } from "react";
import { Menu } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  onMenuClick?: () => void;
}

function Header({ title, subtitle, actions, onMenuClick }: HeaderProps) {
  return (
    <header className="py-5 md:py-8 px-6 md:px-10 lg:px-12 border-b border-border/40 bg-surface/30 backdrop-blur-xl sticky top-0 z-20">
      <div className="w-full max-w-[1400px] mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4 sm:gap-0">
        <div className="flex items-center gap-4">
          {onMenuClick && (
            <button 
              onClick={onMenuClick} 
              className="md:hidden p-1.5 -ml-1.5 text-text-secondary hover:text-text hover:bg-surface-elevated rounded-lg transition-colors"
            >
              <Menu size={24} />
            </button>
          )}
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-text flex items-center gap-2">
              <span className="gradient-text-primary">{title}</span>
            </h1>
            {subtitle && (
              <p className="text-sm text-text-secondary mt-1 font-medium">{subtitle}</p>
            )}
          </div>
        </div>

        {actions && <div className="flex items-center gap-3">{actions}</div>}
      </div>
    </header>
  );
}

export default Header;

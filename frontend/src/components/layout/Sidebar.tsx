/**
 * Sidebar Component
 *
 * Left navigation sidebar displaying logo, primary navigation links,
 * active link indicator, and user authentication status footer.
 */

import { useState } from "react";
import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "../../lib/constants";
import { useAuth } from "../../contexts/AuthContext";
import LoginModal from "../shared/LoginModal";
import RegisterModal from "../shared/RegisterModal";
import {
  LayoutDashboard,
  Search,
  FileText,
  SlidersHorizontal,
  ClipboardList,
  LogIn,
  LogOut,
  X,
} from "lucide-react";
import { getInitials } from "../../lib/utils";

const ICON_MAP: Record<string, React.ElementType> = {
  LayoutDashboard,
  Search,
  FileText,
  SlidersHorizontal,
  ClipboardList,
};

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  onToggle?: () => void;
}

function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const { user, isAuthenticated, logout } = useAuth();
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Sidebar Content */}
      <aside 
        className={`w-[240px] h-screen bg-surface border-r border-border flex flex-col fixed left-0 top-0 z-50 transition-transform duration-300 ease-in-out md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* App Logo & Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-[10px] bg-primary flex items-center justify-center font-bold text-white text-base shadow-sm">
              F
            </div>
            <div>
              <h1 className="text-base font-extrabold tracking-tight text-text">
                Finder
              </h1>
              <span className="text-[10px] text-text-muted font-medium uppercase tracking-wider block -mt-1">
                AI Job Assistant
              </span>
            </div>
          </div>
          <button 
            className="md:hidden text-text-secondary hover:text-text p-1"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const IconComponent = ICON_MAP[item.icon] || Search;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                onClick={() => onClose?.()}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 h-10 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "bg-surface-elevated text-text shadow-sm"
                      : "text-text-secondary hover:text-text hover:bg-surface-elevated/50"
                  }`
                }
              >
                <IconComponent size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="p-4 border-t border-border">
          {isAuthenticated && user ? (
            <div className="p-2 rounded-xl bg-surface-elevated/30 border border-border flex items-center justify-between">
              <div className="flex items-center gap-3 min-w-0 px-1">
                <div className="h-8 w-8 rounded-full bg-surface-elevated text-text border border-border flex items-center justify-center font-medium text-xs shrink-0">
                  {getInitials(user.full_name)}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-text truncate">
                    {user.full_name}
                  </p>
                  <p className="text-xs text-text-muted truncate">
                    {user.email}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={logout}
                title="Sign Out"
                className="p-2 rounded-lg text-text-muted hover:text-error hover:bg-error/10 transition-colors cursor-pointer"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() => setIsLoginOpen(true)}
                className="w-full h-10 rounded-lg bg-surface-elevated border border-border text-sm font-medium text-text hover:bg-surface-hover transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <LogIn size={16} />
                Sign In
              </button>
            </div>
          )}
        </div>

        {/* Auth Modals */}
        <LoginModal
          isOpen={isLoginOpen}
          onClose={() => setIsLoginOpen(false)}
          onSwitchToRegister={() => {
            setIsLoginOpen(false);
            setIsRegisterOpen(true);
          }}
        />

        <RegisterModal
          isOpen={isRegisterOpen}
          onClose={() => setIsRegisterOpen(false)}
          onSwitchToLogin={() => {
            setIsRegisterOpen(false);
            setIsLoginOpen(true);
          }}
        />
      </aside>
    </>
  );
}

export default Sidebar;

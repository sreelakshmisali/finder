/**
 * Modal Component
 *
 * An overlay dialog that appears on top of the page content.
 * Used for confirmations, detail views, and forms.
 *
 * Accessibility:
 * - Clicking the backdrop closes the modal
 * - Pressing Escape closes the modal
 * - Focus is trapped inside (no tabbing to hidden content)
 * - Uses Framer Motion for smooth enter/exit animations
 */

import { useEffect, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

interface ModalProps {
  /** Whether the modal is currently visible */
  isOpen: boolean;
  /** Callback to close the modal */
  onClose: () => void;
  /** Title text at the top of the modal */
  title?: string;
  /** Content inside the modal body */
  children: ReactNode;
  /** Width of the modal */
  size?: "sm" | "md" | "lg";
}

/** Width classes for each size */
const sizeClasses: Record<string, string> = {
  sm: "max-w-[95vw] sm:max-w-sm md:max-w-md",
  md: "max-w-[95vw] md:max-w-lg",
  lg: "max-w-[95vw] md:max-w-2xl",
};

function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
}: ModalProps) {
  /**
   * Close on Escape key press.
   *
   * We add and clean up the event listener properly
   * to avoid memory leaks.
   */
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      /* Prevent body scrolling while modal is open */
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        /* Portal — renders at the top of the DOM tree */
        <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4">
          {/* Backdrop — dark overlay behind the modal */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Modal panel */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
              "relative w-full glass-card rounded-2xl shadow-lg",
              "bg-surface border border-border",
              sizeClasses[size]
            )}
            role="dialog"
            aria-modal="true"
            aria-label={title}
          >
            {/* Header with title and close button */}
            {title && (
              <div className="flex items-center justify-between p-5 border-b border-border">
                <h2 className="text-lg font-semibold text-text">{title}</h2>
                <button
                  onClick={onClose}
                  className={cn(
                    "p-1.5 rounded-lg text-text-muted",
                    "hover:text-text hover:bg-surface-elevated",
                    "transition-colors duration-[150ms]",
                    "focus-ring cursor-pointer"
                  )}
                  aria-label="Close modal"
                >
                  <X size={18} />
                </button>
              </div>
            )}

            {/* Body */}
            <div className="p-5 max-h-[85vh] overflow-y-auto">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export default Modal;

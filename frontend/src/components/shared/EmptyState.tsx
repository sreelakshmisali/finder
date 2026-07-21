/**
 * EmptyState Component
 *
 * Displayed when a page or section has no data yet.
 * For example: "No jobs found" or "Upload your first resume".
 *
 * Why have a dedicated component?
 * - Blank screens confuse users — they wonder if something broke
 * - Empty states are an opportunity to guide the user's next action
 * - Consistent styling across all empty states
 */

import { type ReactNode } from "react";
import { motion } from "framer-motion";

interface EmptyStateProps {
  /** Icon to display at the top */
  icon: ReactNode;
  /** Main heading — explains what's missing */
  title: string;
  /** Description — provides more context */
  description: string;
  /** Optional action button (e.g., "Upload Resume") */
  action?: ReactNode;
}

/**
 * EmptyState — a friendly placeholder for empty pages.
 *
 * @example
 *   <EmptyState
 *     icon={<FileText size={48} />}
 *     title="No resumes yet"
 *     description="Upload your resume to get started"
 *     action={<Button>Upload Resume</Button>}
 *   />
 */
function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="flex flex-col items-center justify-center py-12 md:py-20 px-4 text-center"
    >
      {/* Icon — large, muted color */}
      <div className="mb-4 text-text-muted">{icon}</div>

      {/* Title */}
      <h3 className="text-lg font-semibold text-text mb-2">{title}</h3>

      {/* Description */}
      <p className="text-sm text-text-secondary max-w-sm mb-6">
        {description}
      </p>

      {/* Action button (optional) */}
      {action && <div>{action}</div>}
    </motion.div>
  );
}

export default EmptyState;

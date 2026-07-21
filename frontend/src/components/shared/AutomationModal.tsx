/**
 * AutomationModal Component
 *
 * Interactive step-by-step Playwright application assistant:
 * 1. Progress step indicators (1. Navigating & Filling -> 2. Review -> 3. Confirm Submit).
 * 2. Filled fields summary pills (Name, Email, Resume file).
 * 3. Custom question input fields if required.
 * 4. EXPLICIT USER APPROVAL BUTTON ("Confirm & Submit Application").
 */

import { useState } from "react";
import type { Application } from "../../types/application";
import type { AutomationStateResponse } from "../../types/automation";
import { Button, Spinner, Badge } from "../ui";
import {
  CheckCircle2,
  AlertTriangle,
  Play,
  ShieldCheck,
  Building2,
  FileCheck,
  HelpCircle,
  Zap,
} from "lucide-react";

interface AutomationModalProps {
  application: Application;
  automationState: AutomationStateResponse | null;
  onStartAutomation: () => void;
  onConfirmSubmit: (answers: Record<string, string>) => void;
  isStarting: boolean;
  isSubmitting: boolean;
}

function AutomationModal({
  application,
  automationState,
  onStartAutomation,
  onConfirmSubmit,
  isStarting,
  isSubmitting,
}: AutomationModalProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const handleAnswerChange = (questionId: string, val: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: val }));
  };

  const handleFinalSubmit = () => {
    onConfirmSubmit(answers);
  };

  const isFormFilled = automationState?.status === "awaiting_confirmation" || automationState?.status === "completed";
  const customQuestions = automationState?.custom_questions || [];
  const filledSummary = automationState?.filled_fields_summary || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 glass rounded-[20px] flex items-center justify-between gap-6 shadow-sm">
        <div>
          <h3 className="text-xl font-bold text-text mb-1">{application.job.title}</h3>
          <p className="text-sm text-primary font-semibold flex items-center gap-1.5">
            <Building2 size={16} /> {application.job.company} • {application.job.location}
          </p>
        </div>
        <Badge variant="accent" className="capitalize text-xs">
          {application.job.source} Automator
        </Badge>
      </div>

      {/* Safety Guarantee Callout */}
      <div className="p-5 rounded-[16px] bg-primary-muted/15 border border-primary/30 flex items-start gap-4 text-sm text-text shadow-sm">
        <ShieldCheck size={24} className="text-primary shrink-0 mt-0.5" />
        <div>
          <strong className="text-primary font-semibold block mb-1">Human-in-the-Loop Safety Guarantee:</strong>
          Finder fills form details and attaches your resume, but will <strong>NEVER submit</strong> without your explicit click below.
        </div>
      </div>

      {/* Step 1: Initial State / Launch */}
      {!automationState && (
        <div className="py-8 text-center space-y-4">
          <div className="h-16 w-16 rounded-full bg-primary-muted text-primary flex items-center justify-center mx-auto">
            <Play size={28} />
          </div>
          <div>
            <h4 className="text-base font-semibold text-text">Ready to Fill Application Form</h4>
            <p className="text-xs text-text-secondary max-w-md mx-auto mt-1">
              Playwright browser will navigate to {application.job.company}'s application page, fill candidate details, and attach your active PDF resume.
            </p>
          </div>

          <Button
            variant="primary"
            size="lg"
            onClick={onStartAutomation}
            isLoading={isStarting}
            icon={<Zap size={18} />}
          >
            Start Playwright Assistant
          </Button>
        </div>
      )}

      {/* Loading Progress State */}
      {isStarting && (
        <div className="py-12 flex flex-col items-center justify-center space-y-3">
          <Spinner size="lg" />
          <p className="text-sm font-semibold text-text">
            Playwright browser filling form fields & attaching active PDF resume...
          </p>
        </div>
      )}

      {/* Step 2: Form Filled & Summary Review */}
      {automationState && !isStarting && (
        <div className="space-y-5">
          {/* Filled Summary List */}
          {filledSummary.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <FileCheck size={14} className="text-success" /> Auto-Filled Details Summary
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {filledSummary.map((item, i) => (
                  <div key={i} className="p-2.5 rounded-[10px] bg-surface-elevated/60 border border-border text-xs text-text flex items-center gap-2">
                    <CheckCircle2 size={14} className="text-success shrink-0" />
                    <span className="truncate">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Custom Questions if present */}
          {customQuestions.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <HelpCircle size={14} className="text-warning" /> Custom Questions Answer Required
              </h4>
              <div className="space-y-3">
                {customQuestions.map((q) => (
                  <div key={q.id} className="space-y-1">
                    <label className="text-xs font-medium text-text block">
                      {q.label} {q.required && <span className="text-error">*</span>}
                    </label>
                    <input
                      type="text"
                      value={answers[q.id] || ""}
                      onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                      placeholder="Your answer..."
                      className="w-full bg-surface border border-border rounded-[8px] p-2 text-xs text-text focus:outline-none focus:border-primary"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Final Explicit Submit Approval Section */}
          {isFormFilled && (
            <div className="pt-4 border-t border-border flex items-center justify-between gap-3">
              <div className="text-xs text-text-muted flex items-center gap-1">
                <AlertTriangle size={14} className="text-warning" /> Ready for final submission
              </div>

              <Button
                variant="primary"
                size="lg"
                onClick={handleFinalSubmit}
                isLoading={isSubmitting}
                icon={<CheckCircle2 size={18} />}
              >
                Confirm & Submit Application
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AutomationModal;

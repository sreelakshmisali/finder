/**
 * ResumeOnboardingCard Component
 *
 * Prominent Dashboard banner presented to candidates who do not have an active PDF resume.
 * Guides candidate through: Upload -> AI Parse -> Explore Matching Jobs flow.
 * Reuses existing ResumeUploader component for drag-and-drop file ingestion.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ResumeUploader from "./ResumeUploader";
import { useUploadResume, useParseResume } from "../../hooks/useResume";
import { Button, Spinner } from "../ui";
import type { Resume, ParsedResumeData } from "../../types/resume";
import {
  Sparkles,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Zap,
  AlertCircle,
} from "lucide-react";

export default function ResumeOnboardingCard() {
  const navigate = useNavigate();
  const uploadMutation = useUploadResume();
  const parseMutation = useParseResume();

  const [step, setStep] = useState<"idle" | "uploading" | "parsing" | "complete">("idle");
  const [parsedResume, setParsedResume] = useState<Resume | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    setErrorMsg(null);
    setStep("uploading");

    try {
      // Step 1: Save resume file & set active
      const uploaded = await uploadMutation.mutateAsync(file);

      // Step 2: Parse resume with AI
      setStep("parsing");
      const parsed = await parseMutation.mutateAsync(uploaded.id);

      // Step 3: Complete
      setParsedResume(parsed);
      setStep("complete");
    } catch (err: any) {
      setStep("idle");
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to upload or parse resume. Please try again.";
      setErrorMsg(msg);
    }
  };

  const parsedData = parsedResume?.parsed_data as ParsedResumeData | undefined;
  const extractedSkillsCount = parsedData?.skills?.length || 0;

  return (
    <div className="relative overflow-hidden rounded-3xl bg-surface border-2 border-primary/30 shadow-xl p-6 sm:p-8 lg:p-10 space-y-8 backdrop-blur-md">
      {/* Background Subtle Gradient Glow */}
      <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header Banner */}
      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-border/60">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary/15 border border-primary/30 text-xs font-extrabold text-primary uppercase tracking-wider">
            <Zap size={14} className="animate-pulse" /> Mandatory Core Step
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-text tracking-tight">
            Upload Your Resume to Unlock <span className="text-primary">AI Job Matching</span>
          </h2>
          <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
            Finder requires an active PDF resume to calculate skill alignment scores, detect missing qualifications, and power automated applications.
          </p>
        </div>

        {/* Visual Workflow Steps */}
        <div className="flex items-center gap-2 sm:gap-4 shrink-0 bg-surface-elevated/60 p-3 rounded-2xl border border-border/50 text-xs font-semibold">
          <div className={`flex items-center gap-1.5 ${step === "idle" || step === "uploading" ? "text-primary font-bold" : "text-text-muted"}`}>
            <span className="h-6 w-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-bold">1</span>
            Upload
          </div>
          <span className="text-border">→</span>
          <div className={`flex items-center gap-1.5 ${step === "parsing" ? "text-accent font-bold" : "text-text-muted"}`}>
            <span className="h-6 w-6 rounded-full bg-accent/20 text-accent flex items-center justify-center text-xs font-bold">2</span>
            AI Parse
          </div>
          <span className="text-border">→</span>
          <div className={`flex items-center gap-1.5 ${step === "complete" ? "text-success font-bold" : "text-text-muted"}`}>
            <span className="h-6 w-6 rounded-full bg-success/20 text-success flex items-center justify-center text-xs font-bold">3</span>
            Jobs Ready
          </div>
        </div>
      </div>

      {/* Main Content Body */}
      <div className="relative z-10">
        {step === "complete" ? (
          /* Step 3: Success Completion View */
          <div className="p-8 rounded-2xl bg-success/10 border border-success/30 text-center space-y-6 animate-in fade-in duration-300">
            <div className="h-16 w-16 rounded-full bg-success/20 text-success flex items-center justify-center mx-auto shadow-md">
              <CheckCircle2 size={36} />
            </div>

            <div className="space-y-2 max-w-md mx-auto">
              <h3 className="text-2xl font-black text-text">
                Resume Parsed Successfully!
              </h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                Extracted <strong className="text-text font-bold">{extractedSkillsCount} key skills</strong> and profile details from <span className="font-semibold text-primary">{parsedResume?.filename}</span>.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
              <Button
                variant="primary"
                size="lg"
                onClick={() => navigate("/jobs")}
                icon={<Sparkles size={18} />}
                className="w-full sm:w-auto px-8 py-3.5 text-base font-bold shadow-lg shadow-primary/25"
              >
                Explore Matching Jobs <ArrowRight size={18} className="ml-1" />
              </Button>
            </div>
          </div>
        ) : step === "uploading" || step === "parsing" ? (
          /* Processing State View */
          <div className="p-12 rounded-2xl bg-surface-elevated border border-border text-center space-y-4">
            <Spinner size="lg" className="mx-auto" />
            <div className="space-y-1">
              <h4 className="text-lg font-bold text-text">
                {step === "uploading" ? "Saving PDF Resume..." : "Extracting Skills & Experience with AI..."}
              </h4>
              <p className="text-xs text-text-muted">
                {step === "uploading" ? "Writing file to secure storage..." : "Analyzing text structure and populating skills matrix..."}
              </p>
            </div>
          </div>
        ) : (
          /* Upload State View */
          <div className="space-y-4">
            <ResumeUploader
              onUpload={handleUpload}
              isLoading={uploadMutation.isPending || parseMutation.isPending}
            />

            {errorMsg && (
              <div className="p-4 rounded-xl bg-error/10 border border-error/20 flex items-center gap-3 text-xs text-error font-medium">
                <AlertCircle size={16} className="shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Info Pill */}
      <div className="relative z-10 flex items-center justify-between text-xs text-text-muted pt-2 border-t border-border/40">
        <span className="flex items-center gap-1.5 font-medium">
          <ShieldCheck size={14} className="text-success" />
          PDF Encryption & Private Data Isolation Enabled
        </span>
        <span className="hidden sm:inline">Preferences remain optional</span>
      </div>
    </div>
  );
}

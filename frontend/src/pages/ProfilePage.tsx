/**
 * ProfilePage Component
 *
 * Unified Profile Setup Page combining:
 * 1. Resume Section (Candidate Capability) — Required
 * 2. Preferences Section (Candidate Goals) — Optional
 */

import Header from "../components/layout/Header";
import PageWrapper from "../components/layout/PageWrapper";
import ProfileCompletionCard from "../components/profile/ProfileCompletionCard";
import ResumeSection from "../components/profile/ResumeSection";
import { Spinner } from "../components/ui";
import { useProfileSetup } from "../hooks/useProfile";

export default function ProfilePage() {
  const { data: profileData, isLoading, isError } = useProfileSetup();

  return (
    <>
      <Header
        title="Profile Setup"
        subtitle="Manage your PDF resume capabilities in one place"
      />

      <PageWrapper>
        <div className="max-w-7xl mx-auto space-y-8 w-full p-6 lg:p-12">
          {/* Loading Spinner */}
          {isLoading && (
             <div className="flex justify-center py-24">
               <Spinner size="lg" />
             </div>
          )}

          {/* Error State */}
          {isError && (
            <div className="p-4 rounded-xl bg-error/15 border border-error/30 text-error text-sm font-medium">
              Failed to load profile setup data. Check backend connection.
            </div>
          )}

          {!isLoading && (
            <>
              {/* Profile Completion Overview Header */}
              <ProfileCompletionCard data={profileData} />

              {/* Section 1: Resume Capabilities (Required) */}
              <ResumeSection summary={profileData?.resume_summary} />
            </>
          )}
        </div>
      </PageWrapper>
    </>
  );
}

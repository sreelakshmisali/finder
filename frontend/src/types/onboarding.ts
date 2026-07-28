/**
 * Onboarding Status Type Definition
 */

export interface OnboardingStatus {
  account_created?: boolean;
  resume_uploaded?: boolean;
  resume_analyzed?: boolean;
  has_active_resume: boolean;
  profile_completion_percentage: number;
}

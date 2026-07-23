/**
 * Onboarding Status Type Definition
 */

export interface OnboardingStatus {
  account_created?: boolean;
  resume_uploaded?: boolean;
  resume_analyzed?: boolean;
  preferences_configured?: boolean;
  has_active_resume: boolean;
  has_preferences: boolean;
  profile_completion_percentage: number;
}

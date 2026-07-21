/**
 * Automation TypeScript Type Definitions
 */

export interface AutomationQuestion {
  id: string;
  label: string;
  field_type: "text" | "select" | "checkbox" | string;
  required: boolean;
  options?: string[] | null;
  value?: string | null;
}

export interface AutomationStateResponse {
  application_id: string;
  status: string;
  step_summary: string;
  custom_questions: AutomationQuestion[];
  filled_fields_summary: string[];
}

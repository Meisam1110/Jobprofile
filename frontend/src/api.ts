/** API client + shared types. Token persisted in localStorage. */

export interface Grade { id: number; code: string; rank: number; band: string }
export interface NamedRef { id: number; name: string }
export interface ProfileSummary {
  id: number; job_title: string; job_code: string; location: string;
  reports_to: string; direct_reports: number; status: string; is_active: boolean;
  version: number; updated_at: string; approved_date: string | null;
  grade: Grade | null; role_family: NamedRef | null; job_family: NamedRef | null;
  division: NamedRef | null; department: NamedRef | null;
}
export interface Responsibility { id?: number; text: string; pct_time: number | null; frequency: string; key_tasks: string; deliverables: string; decision_authority: string; sort_order: number }
export interface KPI { id?: number; name: string; kpi_type: string; weight: number | null; owner: string; formula: string; measurement_method: string }
export interface ProfileCompetency { id: number; competency: { id: number; name: string; comp_type: string; category: string }; required_level: string; desired_level: string; importance: string; assessment_method: string }
export interface ProfileSkill { id: number; skill: { id: number; name: string; category: string }; requirement: string; level: number }
export interface Qualification { id?: number; qual_type: string; text: string; mandatory: boolean }
export interface ProfileDetail extends ProfileSummary {
  position_code: string; sub_family: string; band: string; org_level: string;
  employment_type: string; job_category: string; language: string;
  mission: string; context: string; business_value: string; success_definition: string;
  responsibilities_text: string; collaboration_text: string; authorities_text: string;
  education_text: string; experience_text: string; trainings_text: string;
  behavioral_text: string; working_conditions: string; performance_standards: string;
  collaboration: Record<string, string>; authority_matrix: unknown[];
  success_profile: Record<string, unknown>; work_conditions: Record<string, unknown>;
  signoff: Record<string, string>; custom_fields: Record<string, unknown>;
  document_version: string; source_file: string; created_at: string;
  responsibilities: Responsibility[]; kpis: KPI[];
  profile_competencies: ProfileCompetency[]; profile_skills: ProfileSkill[];
  qualifications: Qualification[];
}
export interface Paged<T> { total: number; page: number; page_size: number; items: T[] }
export interface Taxonomy {
  grades: Grade[]; divisions: (NamedRef & { code: string })[]; role_families: NamedRef[];
  job_families: NamedRef[]; statuses: string[]; competency_types: string[]; competency_levels: string[];
}
export interface User { token: string; username: string; full_name: string; role: string }
export interface WorkflowEvent { id: number; event_type: string; from_state: string; to_state: string; actor: string; actor_role: string; comment: string; created_at: string }
export interface Version { id: number; version_no: number; change_note: string; changed_by: string; created_at: string }
export interface CareerEdge { id: number; profile_id: number; title: string; grade: string; path_type: string; direction: string; promotion_criteria: string; readiness_level: string }
export interface Notification { id: number; notif_type: string; message: string; profile_id: number | null; is_read: boolean; created_at: string }
export interface SearchHit { id: number; job_title: string; location: string; status: string; grade: string; match: string }

const TOKEN_KEY = "jpms_user";

export function currentUser(): User | null {
  const raw = localStorage.getItem(TOKEN_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}
export function setUser(user: User | null) {
  if (user) localStorage.setItem(TOKEN_KEY, JSON.stringify(user));
  else localStorage.removeItem(TOKEN_KEY);
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const user = currentUser();
  const headers: Record<string, string> = {
    "content-type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (user) headers["Authorization"] = `Bearer ${user.token}`;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch { /* keep statusText */ }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function exportUrl(profileId: number, fmt: string): string {
  return `/api/profiles/${profileId}/export?fmt=${fmt}`;
}

export const SERIES = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948"];
export const SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#1c5cab", "#104281"];

export const STATUS_COLORS: Record<string, string> = {
  Draft: "bg-gray-200 text-gray-800",
  "Under Review": "bg-amber-100 text-amber-900",
  "HR Review": "bg-amber-100 text-amber-900",
  "Business Review": "bg-amber-100 text-amber-900",
  "Organization Design Review": "bg-amber-100 text-amber-900",
  "Compensation Review": "bg-amber-100 text-amber-900",
  "Executive Approval": "bg-blue-100 text-blue-900",
  Published: "bg-green-100 text-green-900",
  Archived: "bg-gray-100 text-gray-500",
};

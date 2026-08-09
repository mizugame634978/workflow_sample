/** Mirrors the FastAPI response models in `backend/app/schemas`. */

export type RequestStatus = "draft" | "pending" | "approved" | "rejected" | "cancelled";

export type StepStatus =
  | "waiting"
  | "pending"
  | "approved"
  | "rejected"
  | "sent_back"
  | "skipped";

export type AuditAction =
  | "created"
  | "updated"
  | "submitted"
  | "approved"
  | "rejected"
  | "sent_back"
  | "cancelled"
  | "commented";

export type NotificationType =
  | "approval_requested"
  | "step_approved"
  | "completed"
  | "rejected"
  | "sent_back"
  | "commented";

export type UserRole = "admin" | "member";

export type FieldType = "text" | "textarea" | "number" | "date" | "select";

export type ApproverType = "user" | "manager" | "role";

export interface UserRef {
  id: number;
  name: string;
  email: string;
  department: string;
  job_title: string;
}

export interface User extends UserRef {
  role: UserRole;
  is_active: boolean;
  manager: UserRef | null;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
}

export interface Profile extends User {
  organization: Organization;
}

export interface FormField {
  key: string;
  label: string;
  type: FieldType;
  required?: boolean;
  help_text?: string;
  options?: string[];
  placeholder?: string;
  min?: number | null;
  max?: number | null;
  max_length?: number | null;
}

export interface TemplateStep {
  id: number;
  order_index: number;
  name: string;
  approver_type: ApproverType;
  approver_role: UserRole | null;
  approver: UserRef | null;
}

export interface TemplateSummary {
  id: number;
  code: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  is_active: boolean;
  step_count: number;
  created_at: string;
}

export interface TemplateDetail extends TemplateSummary {
  form_fields: FormField[];
  steps: TemplateStep[];
}

export interface RequestStep {
  id: number;
  order_index: number;
  name: string;
  status: StepStatus;
  approver: UserRef | null;
  approver_role: UserRole | null;
  comment: string | null;
  acted_by: UserRef | null;
  acted_at: string | null;
}

export interface TimelineEntry {
  id: number;
  action: AuditAction;
  actor: UserRef | null;
  from_status: RequestStatus | null;
  to_status: RequestStatus | null;
  step_name: string | null;
  comment: string | null;
  created_at: string;
}

export interface Comment {
  id: number;
  body: string;
  created_at: string;
  user: UserRef;
}

export interface RequestPermissions {
  can_edit: boolean;
  can_submit: boolean;
  can_approve: boolean;
  can_cancel: boolean;
  can_comment: boolean;
}

export interface RequestSummary {
  id: number;
  request_number: string;
  title: string;
  status: RequestStatus;
  template_id: number;
  template_name: string;
  template_category: string;
  applicant: UserRef;
  current_step_name: string | null;
  current_approver_name: string | null;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  completed_at: string | null;
}

export interface RequestDetail extends RequestSummary {
  form_data: Record<string, unknown>;
  current_step_index: number;
  round_no: number;
  last_send_back_comment: string | null;
  template: {
    id: number;
    code: string;
    name: string;
    category: string;
    description: string;
    form_fields: FormField[];
  };
  steps: RequestStep[];
  comments: Comment[];
  timeline: TimelineEntry[];
  permissions: RequestPermissions;
}

export interface Notification {
  id: number;
  type: NotificationType;
  message: string;
  is_read: boolean;
  created_at: string;
  request: { id: number; request_number: string; title: string; status: RequestStatus };
}

export interface AnalyticsSummary {
  by_status: Record<RequestStatus, number>;
  my_open_requests: number;
  awaiting_my_approval: number;
  total_requests: number;
  average_lead_time_hours: number;
  monthly: { month: string; count: number }[];
  by_template: { name: string; count: number }[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ItemList<T> {
  items: T[];
}

export interface ApiError {
  message: string;
  errors: Record<string, string>;
}

export interface User {
    id: string;
    name: string;
    email: string;
    role: UserRole;
    created_at: string;
}

export type UserRole = "STUDENT" | "TA" | "ADMIN";

export type TicketStatus =
    | "OPEN"
    | "CLAIMED"
    | "IN_PROGRESS"
    | "RESOLVED"
    | "CANCELLED";

// Auth
export interface RegisterRequest {
    name: string;
    email: string;
    password: string;
    role?: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
}

export interface Course {
    id: string;
    code: string;
    name: string;
    created_at: string;
    staff?: User[];
}

export interface CourseCreate {
    code: string;
    name: string;
}

export interface OfficeHoursSession {
    id: string;
    course_id: string;
    starts_at: string;
    ends_at: string;
    is_active: boolean;
    created_at: string;
}

export interface SessionCreate {
    course_id: string;
    starts_at: string;
    ends_at: string;
}

export interface SessionStats {
    count_open: number;
    count_claimed: number;
    count_in_progress: number;
    count_resolved: number;
    count_cancelled: number;
    avg_wait_time_seconds: number | null;
    median_wait_time_seconds: number | null;
    avg_time_to_resolve_seconds: number | null;
}

export interface Ticket {
    id: string;
    session_id: string;
    course_id: string;
    student_id: string;
    assigned_ta_id: string | null;
    title: string;
    description: string;
    topic_tag: string | null;
    status: TicketStatus;
    created_at: string;
    claimed_at: string | null;
    started_at: string | null;
    resolved_at: string | null;
    cancelled_at: string | null;
}

export interface TicketCreate {
    session_id: string;
    title: string;
    description: string;
    topic_tag?: string;
}

export interface TicketCreate {
    session_id: string;
    title: string;
    description: string;
    topic_tag?: string;
}

export interface DuplicateTicket {
    ticket_id: string;
    title: string;
    status: string;
    similarity: number;
    student_id: string | null;
    created_at: string;
}

export interface TicketCreateResponse {
    ticket: Ticket;
    possible_duplicates: DuplicateTicket[];
}

export interface APIError {
    detail: string | { loc: string[]; msg: string; type: string }[];
}

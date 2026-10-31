/**
 * Shared TypeScript type definitions for LegalJarvis frontend.
 */

export type UserRole = "researcher" | "citizen" | "reviewer" | "admin";

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface SearchItem {
  chunk_id: number;
  document_id: number;
  title: string;
  court: string;
  decision_date: string | null;
  neutral_citation: string | null;
  para_no: number | null;
  segment_type: string | null;
  snippet: string;
  score: number;
  attribution: string;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchItem[];
  attribution: string;
}

export interface SearchRequest {
  query: string;
  mode?: "hybrid" | "lexical" | "dense";
  court_codes?: string[];
  year_from?: number;
  year_to?: number;
  rerank?: boolean;
  limit?: number;
  offset?: number;
}

export interface QACitation {
  marker: string; // e.g. "[C1]"
  chunk_id: number;
  document_id: number;
  title: string;
  court: string;
  neutral_citation?: string | null;
  para_no?: number | null;
  snippet: string;
  attribution: string;
}

export interface QAResponse {
  question: string;
  answer: string;
  citations: QACitation[];
  abstained: boolean;
  abstention_reason?: string | null;
  criminal_transition_notice?: string | null;
  disclaimer: string;
  generation_status: "completed" | "abstained" | "generation_unavailable";
}

export interface QARequest {
  question: string;
  court_codes?: string[];
  year_from?: number;
  year_to?: number;
}

export interface ChunkOut {
  id: number;
  para_no: number | null;
  segment_type: string | null;
  text: string;
  start_char: number;
  end_char: number;
}

export interface DocumentDetail {
  id: number;
  title: string;
  court_code: string;
  court_name?: string | null;
  decision_date?: string | null;
  neutral_citation?: string | null;
  bench?: string | null;
  dataset_name: string;
  extraction_quality?: number | null;
  text: string;
  chunks: ChunkOut[];
  attribution: string;
}

export interface FeedbackCreate {
  answer_id?: number | null;
  query?: string | null;
  rating: number; // 1 or -1
  label?: "supported" | "unsupported" | "hallucinated" | "incomplete" | "wrong_law" | null;
  notes?: string | null;
}

export interface FeedbackResponse {
  id: number;
  status: string;
  message: string;
}

export interface HistoryItem {
  id: string;
  timestamp: string;
  query: string;
  answer: string;
  abstained: boolean;
  citationsCount: number;
  criminalNotice?: string | null;
}

// ==========================================
// Petition Generator Types (Task T-19)
// ==========================================

export type PetitionType =
  | "writ_petition"
  | "bail_application"
  | "pil"
  | "civil_petition"
  | "criminal_revision"
  | "custom_petition";

export interface PartyInput {
  name: string;
  age?: string;
  relation?: string;
  address: string;
  role: string;
  phone?: string;
  email?: string;
  advocate_name?: string;
  advocate_bar_id?: string;
}

export interface EventInput {
  date: string;
  description: string;
}

export interface PreviousOrderInput {
  court: string;
  date: string;
  summary: string;
}

export interface AnnexureInput {
  mark: string;
  title: string;
  description?: string;
}

export interface PetitionFormData {
  petition_type: PetitionType;
  court_level: "supreme_court" | "high_court" | "district_court";
  court_name: string;
  state_ut?: string;
  category: "constitutional" | "criminal" | "civil" | "special_leave";
  case_number?: string;
  statutory_provisions?: string;
  petitioners: PartyInput[];
  respondents: PartyInput[];
  dispute_background: string;
  events: EventInput[];
  previous_orders: PreviousOrderInput[];
  annexures: AnnexureInput[];
  grounds: string[];
  rights_infringed: string[];
  statutes_applied: string[];
  urgency_reason?: string;
  limitation_explanation?: string;
  main_prayers: string[];
  interim_prayers: string[];
}

export interface PetitionCitation {
  marker: string; // e.g. "[C1]"
  chunk_id?: number | null;
  document_id?: number | null;
  title: string;
  court: string;
  neutral_citation?: string | null;
  para_no?: number | null;
  snippet: string;
  support_status: "verified" | "requires_verification";
  is_binding: boolean;
  relevance_explanation: string;
}

export interface PetitionResponse {
  id?: number | null;
  title: string;
  petition_type: PetitionType;
  court_level: string;
  court_name: string;
  state_ut?: string | null;
  category: string;
  case_number?: string | null;
  sections: Record<string, string>;
  full_text: string;
  citations: PetitionCitation[];
  verification_warnings: string[];
  status: "draft" | "generated" | "reviewed";
  created_at?: string | null;
  updated_at?: string | null;
  disclaimer: string;
}

export interface PetitionDraftListItem {
  id: number;
  title: string;
  petition_type: string;
  court_name: string;
  petitioner_name: string;
  respondent_name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

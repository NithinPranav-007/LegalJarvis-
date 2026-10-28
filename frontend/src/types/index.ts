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

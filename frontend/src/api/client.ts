/**
 * Needhi API client.
 */

import {
  DocumentDetail,
  FeedbackCreate,
  FeedbackResponse,
  PetitionCitation,
  PetitionDraftListItem,
  PetitionFormData,
  PetitionResponse,
  QARequest,
  QAResponse,
  SearchRequest,
  SearchResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem("legaljarvis_token");
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem("legaljarvis_token", token);
    } else {
      localStorage.removeItem("legaljarvis_token");
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private headers(): HeadersInit {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async login(email: string = "reviewer@legaljarvis.local", password: string = "legaljarvis123"): Promise<string> {
    const res = await fetch(`${API_BASE}/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Authentication failed");
    }
    const data = await res.json();
    this.setToken(data.access_token);
    return data.access_token;
  }

  async autoLoginReviewer(): Promise<string | null> {
    if (this.token) return this.token;
    try {
      return await this.login("reviewer@legaljarvis.local", "legaljarvis123");
    } catch {
      return null;
    }
  }

  async search(req: SearchRequest): Promise<SearchResponse> {
    const res = await fetch(`${API_BASE}/v1/search`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({
        query: req.query,
        mode: req.mode || "hybrid",
        court_codes: req.court_codes,
        year_from: req.year_from,
        year_to: req.year_to,
        rerank: req.rerank ?? true,
        limit: req.limit || 20,
        offset: req.offset || 0,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Search failed with status ${res.status}`);
    }
    return res.json();
  }

  async ask(req: QARequest): Promise<QAResponse> {
    const res = await fetch(`${API_BASE}/v1/qa`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Q&A failed with status ${res.status}`);
    }
    return res.json();
  }

  async getDocument(docId: number): Promise<DocumentDetail> {
    const res = await fetch(`${API_BASE}/v1/documents/${docId}`, {
      method: "GET",
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Failed to fetch document #${docId}`);
    }
    return res.json();
  }

  async listDocuments(limit = 20): Promise<Array<{ id: number; title: string; court_code: string; court_name: string; decision_date: string | null; neutral_citation: string | null }>> {
    const res = await fetch(`${API_BASE}/v1/documents?limit=${limit}`, {
      method: "GET",
      headers: this.headers(),
    });
    if (!res.ok) {
      return [];
    }
    return res.json();
  }

  async submitFeedback(feedback: FeedbackCreate): Promise<FeedbackResponse> {
    const res = await fetch(`${API_BASE}/v1/feedback`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(feedback),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Feedback failed with status ${res.status}`);
    }
    return res.json();
  }

  async submitReviewerFeedback(payload: any): Promise<FeedbackResponse> {
    // If no token exists, attempt auto-login
    if (!this.token) {
      await this.autoLoginReviewer().catch(() => { });
    }
    const res = await fetch(`${API_BASE}/v1/feedback/reviewer`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Reviewer feedback failed with status ${res.status}`);
    }
    return res.json();
  }

  async exportFeedback(reviewerOnly: boolean = true): Promise<any[]> {
    if (!this.token) {
      await this.autoLoginReviewer().catch(() => { });
    }
    const res = await fetch(`${API_BASE}/v1/feedback/export?reviewer_only=${reviewerOnly}`, {
      method: "GET",
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Export failed with status ${res.status}`);
    }
    return res.json();
  }

  async uploadDocument(file: File): Promise<{ document_id: number; filename: string; sha256: string; chunk_count: number; expires_at: string }> {
    const formData = new FormData();
    formData.append("file", file);
    const headers: Record<string, string> = {};
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    const res = await fetch(`${API_BASE}/v1/documents/upload`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Upload failed with status ${res.status}`);
    }
    return res.json();
  }

  async deleteDocument(docId: number): Promise<{ status: string; document_id: number }> {
    const res = await fetch(`${API_BASE}/v1/documents/${docId}`, {
      method: "DELETE",
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Deletion failed with status ${res.status}`);
    }
    return res.json();
  }

  async listUserDocuments(): Promise<Array<{ id: number; document_id: number | null; filename: string; sha256: string; status: string; expires_at: string }>> {
    const res = await fetch(`${API_BASE}/v1/documents/user/list`, {
      method: "GET",
      headers: this.headers(),
    });
    if (!res.ok) {
      return [];
    }
    return res.json();
  }

  // ==========================================
  // Petition Generator API Methods
  // ==========================================

  async generatePetition(data: PetitionFormData): Promise<PetitionResponse> {
    const res = await fetch(`${API_BASE}/v1/petitions/generate`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Petition generation failed with status ${res.status}`);
    }
    return res.json();
  }

  async listPetitions(type?: string): Promise<PetitionDraftListItem[]> {
    const url = type
      ? `${API_BASE}/v1/petitions?petition_type=${encodeURIComponent(type)}`
      : `${API_BASE}/v1/petitions`;
    const res = await fetch(url, {
      method: "GET",
      headers: this.headers(),
    });
    if (!res.ok) {
      return [];
    }
    return res.json();
  }

  async getPetition(id: number): Promise<PetitionResponse> {
    const res = await fetch(`${API_BASE}/v1/petitions/${id}`, {
      method: "GET",
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Failed to fetch petition #${id}`);
    }
    return res.json();
  }

  async updatePetition(id: number, data: Partial<PetitionResponse>): Promise<PetitionResponse> {
    const res = await fetch(`${API_BASE}/v1/petitions/${id}`, {
      method: "PUT",
      headers: this.headers(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Failed to update petition #${id}`);
    }
    return res.json();
  }

  async deletePetition(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/v1/petitions/${id}`, {
      method: "DELETE",
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Failed to delete petition #${id}`);
    }
  }

  async regenerateSection(req: {
    petition_id?: number;
    petition_type: string;
    section_key: string;
    custom_instruction?: string;
    current_sections: Record<string, string>;
    draft_metadata?: any;
  }): Promise<{ section_key: string; content: string; citations: PetitionCitation[]; verification_warnings: string[] }> {
    const res = await fetch(`${API_BASE}/v1/petitions/regenerate-section`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Section regeneration failed with status ${res.status}`);
    }
    return res.json();
  }

  getDocxExportUrl(id: number): string {
    return `${API_BASE}/v1/petitions/${id}/export/docx`;
  }

  getPdfExportUrl(id: number): string {
    return `${API_BASE}/v1/petitions/${id}/export/pdf`;
  }

  async exportDirectDocx(payload: { sections: Record<string, string>; title: string }): Promise<Blob> {
    const res = await fetch(`${API_BASE}/v1/petitions/export/direct-docx`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error("Failed to export DOCX document");
    }
    return res.blob();
  }

  async exportDirectPdf(payload: { sections: Record<string, string>; title: string }): Promise<Blob> {
    const res = await fetch(`${API_BASE}/v1/petitions/export/direct-pdf`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error("Failed to export PDF document");
    }
    return res.blob();
  }
}

export const api = new ApiClient();

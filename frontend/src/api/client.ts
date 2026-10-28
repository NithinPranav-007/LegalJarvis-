/**
 * LegalJarvis API client.
 */

import {
  DocumentDetail,
  FeedbackCreate,
  FeedbackResponse,
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
}

export const api = new ApiClient();

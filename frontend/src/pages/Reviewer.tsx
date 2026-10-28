import React, { useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  Award,
  Send,
  HelpCircle,
} from "lucide-react";
import { api } from "../api/client";

interface Props {
  onNavigateHome?: () => void;
}

interface ClaimReviewItem {
  claim_index: number;
  claim_text: string;
  is_supported: boolean;
  cited_para_no: number;
  issue_type: "supported" | "unsupported" | "hallucinated" | "wrong_law";
  notes: string;
}

export const ReviewerPage: React.FC<Props> = () => {
  const [answerId, setAnswerId] = useState<number>(1);
  const [rating, setRating] = useState<number>(5);
  const [label, setLabel] = useState<"supported" | "unsupported" | "hallucinated" | "incomplete" | "wrong_law">("supported");
  const [notes, setNotes] = useState<string>("");
  const [reviewerRole] = useState<string>("advocate");
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [exportCount, setExportCount] = useState<number | null>(null);

  // Sample claims for review demo
  const [claims, setClaims] = useState<ClaimReviewItem[]>([
    {
      claim_index: 0,
      claim_text: "Anticipatory bail under Section 438 CrPC is of wide amplitude and not limited to exceptional cases.",
      is_supported: true,
      cited_para_no: 15,
      issue_type: "supported",
      notes: "Accurate extraction from Gurbaksh Singh Sibbia ¶ 15.",
    },
    {
      claim_index: 1,
      claim_text: "High Court cannot impose arbitrary restrictions not contemplated by statutory text.",
      is_supported: true,
      cited_para_no: 16,
      issue_type: "supported",
      notes: "Fully supported by ¶ 16.",
    },
  ]);

  const handleToggleClaim = (index: number) => {
    setClaims((prev) =>
      prev.map((c, i) =>
        i === index
          ? {
              ...c,
              is_supported: !c.is_supported,
              issue_type: !c.is_supported ? "supported" : "unsupported",
            }
          : c
      )
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/v1/feedback/reviewer", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${api.getToken() || ""}`,
        },
        body: JSON.stringify({
          answer_id: answerId,
          rating,
          overall_label: label,
          claims,
          legal_accuracy_notes: notes,
          reviewer_role: reviewerRole,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP error ${res.status}`);
      }

      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 4000);
    } catch (err: any) {
      setError(err.message || "Failed to submit review");
    }
  };

  const handleExport = async () => {
    try {
      const res = await fetch("http://localhost:8000/v1/feedback/export?reviewer_only=true", {
        headers: {
          Authorization: `Bearer ${api.getToken() || ""}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setExportCount(data.length);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `legaljarvis_gold_labels_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
      }
    } catch (err) {
      console.error("Export failed", err);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Top Banner */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 mb-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-indigo-600 rounded-xl">
              <ShieldCheck className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Legal Reviewer Labelling Portal</h1>
              <p className="text-slate-400 text-sm">
                Certified advocate evaluation and gold-dataset construction (Task T-18 / AS-4)
              </p>
            </div>
          </div>
          <button
            onClick={handleExport}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition-colors"
          >
            <Download className="h-4 w-4" />
            <span>Export Gold Labels {exportCount !== null ? `(${exportCount})` : ""}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Review Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <Award className="h-5 w-5 text-indigo-600" />
              <span>Answer Evaluation</span>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Answer ID under review
                </label>
                <input
                  type="number"
                  min="1"
                  value={answerId}
                  onChange={(e) => setAnswerId(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              {/* Overall verdict */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Overall Legal Accuracy Verdict
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {(
                    [
                      { id: "supported", label: "Supported", desc: "Fully grounded in cited text" },
                      { id: "unsupported", label: "Unsupported", desc: "Claims lack passage evidence" },
                      { id: "hallucinated", label: "Hallucinated", desc: "Fabricated ratio or citation" },
                      { id: "incomplete", label: "Incomplete", desc: "Omitted material holding" },
                      { id: "wrong_law", label: "Wrong Law", desc: "Repealed or overturned rule" },
                    ] as const
                  ).map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setLabel(opt.id)}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        label === opt.id
                          ? "border-indigo-600 bg-indigo-50 text-indigo-900 ring-2 ring-indigo-200"
                          : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                      }`}
                    >
                      <div className="text-sm font-semibold">{opt.label}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* 1-5 Quality Rating */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Overall Faithfulness & Utility Score (1 - 5)
                </label>
                <div className="flex space-x-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className={`w-10 h-10 rounded-lg font-bold text-sm border ${
                        rating === star
                          ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      {star}
                    </button>
                  ))}
                </div>
              </div>

              {/* Per-claim verification checklist */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Per-Claim Grounding Verification
                </label>
                <div className="space-y-3">
                  {claims.map((claim, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-start justify-between gap-3"
                    >
                      <div className="flex-1 text-xs text-slate-800">
                        <div className="font-medium">{claim.claim_text}</div>
                        <div className="mt-1 text-slate-500">
                          Cited: <span className="font-semibold text-slate-700">¶ {claim.cited_para_no}</span> | Note: {claim.notes}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleToggleClaim(idx)}
                        className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-semibold ${
                          claim.is_supported
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        {claim.is_supported ? (
                          <>
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                            <span>Supported</span>
                          </>
                        ) : (
                          <>
                            <XCircle className="h-3.5 w-3.5 text-rose-600" />
                            <span>Unsupported</span>
                          </>
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Reviewer Critique */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Legal Accuracy Notes / Citations Checked
                </label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Note specific discrepancies, missed statutory caveats (e.g. BNS S. 358 savings), or correct ratio..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              {error && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {submitted && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg text-xs flex items-center space-x-2">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>Review recorded successfully! Thank you for contributing to the benchmark.</span>
                </div>
              )}

              <button
                type="submit"
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium text-sm shadow-sm transition-colors flex items-center justify-center space-x-2"
              >
                <Send className="h-4 w-4" />
                <span>Submit Legal Review</span>
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Protocol Guidelines Card */}
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm text-xs text-slate-600 space-y-4">
            <h3 className="font-bold text-slate-900 text-sm flex items-center space-x-1.5">
              <HelpCircle className="h-4 w-4 text-indigo-600" />
              <span>Reviewer Protocols</span>
            </h3>
            <p>
              Per PRD Section G1, LegalJarvis uses certified human labels for accuracy benchmarking. Gold ground truth is never auto-generated by models.
            </p>
            <div className="space-y-2 border-t border-slate-100 pt-3">
              <div className="font-semibold text-slate-800">Key Scrutiny Rules:</div>
              <ul className="list-disc pl-4 space-y-1">
                <li>Check that every factual statement has a matching paragraph citation.</li>
                <li>Verify statutory transition advice quoting BNS S. 358 or BNSS S. 531.</li>
                <li>Label <b>wrong_law</b> if repealed IPC is applied to offenses occurring post 1 July 2024.</li>
                <li>A 20% overlap sample is dual-reviewed for Cohen&apos;s kappa agreement.</li>
              </ul>
            </div>
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-xs">
              <b>Disjointness Notice:</b> Data annotated in this portal is strictly sequestered from retrieval training and model tuning sets.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

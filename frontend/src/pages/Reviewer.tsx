import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  Award,
  Send,
  UserCheck,
  SlidersHorizontal,
} from "lucide-react";
import { api } from "../api/client";
import { SupremeCourt3DCanvas } from "../components/SupremeCourt3DCanvas";
import { RightAuthoritiesPanel } from "../components/RightAuthoritiesPanel";

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
  const [label, setLabel] = useState<
    "supported" | "unsupported" | "hallucinated" | "incomplete" | "wrong_law"
  >("supported");
  const [notes, setNotes] = useState<string>("");
  const [reviewerRole] = useState<string>("advocate");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [exportCount, setExportCount] = useState<number | null>(null);

  // Auto-login reviewer on mount to prevent any 401 Unauthorized errors
  useEffect(() => {
    let isMounted = true;
    api
      .autoLoginReviewer()
      .then(() => {
        if (isMounted) {
          // Token ready
        }
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, []);

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

  // Sample claims for review demo
  const [claims, setClaims] = useState<ClaimReviewItem[]>([
    {
      claim_index: 0,
      claim_text:
        "Anticipatory bail under Section 438 CrPC is of wide amplitude and not limited to exceptional cases.",
      is_supported: true,
      cited_para_no: 15,
      issue_type: "supported",
      notes: "Accurate extraction from Gurbaksh Singh Sibbia ¶ 15.",
    },
    {
      claim_index: 1,
      claim_text:
        "High Court cannot impose arbitrary restrictions not contemplated by statutory text.",
      is_supported: true,
      cited_para_no: 16,
      issue_type: "supported",
      notes: "Fully supported by ¶ 16.",
    },
  ]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.submitReviewerFeedback({
        answer_id: answerId,
        rating,
        overall_label: label,
        claims,
        legal_accuracy_notes: notes,
        reviewer_role: reviewerRole,
      });

      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 4000);
    } catch (err: any) {
      setError(err.message || "Failed to submit review");
    } finally {
      setSubmitting(false);
    }
  };

  const handleExport = async () => {
    try {
      const data = await api.exportFeedback(true);
      setExportCount(data.length);
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `needhi_gold_labels_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
    } catch (err) {
      console.error("Export failed", err);
    }
  };

  return (
    <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 font-sans">
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Column: Review Protocols & Guidelines */}
        <aside
          className="w-full lg:w-64 shrink-0 space-y-6 text-slate-900"
          aria-label="Review Protocols"
        >
          <div className="flex items-center justify-between pb-2 border-b border-slate-300">
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Review Protocols
            </h2>
            <SlidersHorizontal className="h-4 w-4 text-slate-700" />
          </div>

          {/* Key Scrutiny Standards */}
          <div className="space-y-3">
            <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider">
              Scrutiny Standards (PRD G1)
            </label>
            <ul className="space-y-2.5 text-xs text-slate-800 leading-relaxed font-medium">
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#071e17] mt-1.5 shrink-0"></span>
                <span>Check that every factual proposition has a matching paragraph citation.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#071e17] mt-1.5 shrink-0"></span>
                <span>Verify statutory transition advice quoting BNS S. 358 or BNSS S. 531.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#071e17] mt-1.5 shrink-0"></span>
                <span>Label <b className="text-rose-700 font-bold">wrong_law</b> if repealed IPC is applied to offences occurring post 1 July 2024.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#071e17] mt-1.5 shrink-0"></span>
                <span>20% overlap sample is dual-reviewed for Cohen&apos;s kappa agreement.</span>
              </li>
            </ul>
          </div>

          {/* Sequestering Notice */}
          <div className="bg-[#faeae1] border border-[#f3d3be] rounded-xl p-4 text-xs text-[#78350f] space-y-1 shadow-2xs">
            <div className="font-bold text-xs sm:text-sm">Disjointness Notice</div>
            <p className="leading-relaxed font-normal">
              Data annotated in this portal is strictly sequestered from retrieval training and model tuning sets to prevent benchmark contamination.
            </p>
          </div>
        </aside>

        {/* Center Column: Evaluation Form */}
        <div className="flex-1 min-w-0 max-w-3xl space-y-6">
          {/* Hero Banner */}
          <div className="bg-[#edf2ec] border border-[#c2d4c0] rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-5 relative overflow-hidden">
            <div className="flex-1 max-w-xl z-10 space-y-2.5">
              <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#071e17] tracking-tight">
                Legal Reviewer Portal
              </h2>
              <p className="text-sm text-slate-700 font-medium leading-normal">
                Certified advocate evaluation and gold-dataset construction (Task T-18 / AS-4).
              </p>

              <div className="flex flex-wrap items-center gap-2 pt-1 text-xs font-semibold">
                <span className="inline-flex items-center space-x-1.5 bg-[#dcfce7] text-[#14532d] border border-[#86efac] px-3 py-1 rounded-full shadow-3xs">
                  <UserCheck className="h-3.5 w-3.5 text-[#15803d]" />
                  <span>Certified Advocate Session Active</span>
                </span>
                <span className="inline-flex items-center space-x-1.5 bg-[#ffedd5] text-[#78350f] border border-[#fdba74] px-3 py-1 rounded-full shadow-3xs">
                  <ShieldCheck className="h-3.5 w-3.5 text-[#b45309]" />
                  <span>Gold Ground Truth Creation</span>
                </span>
              </div>
            </div>

            <div className="shrink-0 flex items-center justify-center z-10">
              <SupremeCourt3DCanvas className="w-60 h-40" />
            </div>
          </div>

          {/* Main Review Form Card */}
          <div className="bg-white border border-slate-300 rounded-2xl p-6 shadow-sm space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="font-bold text-lg text-slate-950 tracking-tight flex items-center space-x-2">
                <Award className="h-5 w-5 text-[#071e17]" />
                <span>Answer Evaluation</span>
              </h3>
              <button
                type="button"
                onClick={handleExport}
                className="inline-flex items-center space-x-2 px-3.5 py-1.5 bg-[#faeae1] hover:bg-[#f6dec9] text-[#78350f] border border-[#f3d3be] rounded-xl text-xs font-bold transition-all hover:scale-105 shadow-2xs"
              >
                <Download className="h-4 w-4" />
                <span>Export Gold Labels {exportCount !== null ? `(${exportCount})` : ""}</span>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Answer ID */}
              <div>
                <label
                  htmlFor="answer-id-input"
                  className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-1.5"
                >
                  Answer ID under review
                </label>
                <input
                  id="answer-id-input"
                  aria-label="Answer ID under review"
                  type="number"
                  min="1"
                  value={answerId}
                  onChange={(e) => setAnswerId(Number(e.target.value))}
                  className="w-36 bg-white border border-slate-300 rounded-xl px-3.5 py-1.5 text-sm font-bold text-slate-950 focus:outline-none focus:ring-2 focus:ring-[#0f2c24]"
                />
              </div>

              {/* Star / Numeric Rating */}
              <div>
                <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Overall Accuracy Rating (1 - 5)
                </label>
                <div className="flex items-center space-x-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className={`w-10 h-10 rounded-xl text-sm font-bold transition-all hover:scale-105 shadow-3xs ${
                        rating >= star
                          ? "bg-[#071e17] text-white"
                          : "bg-slate-100 text-slate-700 border border-slate-300 hover:bg-slate-200"
                      }`}
                    >
                      {star}★
                    </button>
                  ))}
                  <span className="text-xs font-medium text-slate-600 ml-2">
                    ({rating === 5 ? "Fully accurate & grounded" : rating >= 3 ? "Minor issues" : "Significant errors"})
                  </span>
                </div>
              </div>

              {/* Overall Categorical Label */}
              <div>
                <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Categorical Grounding Label
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {[
                    { id: "supported", label: "Supported", desc: "Every proposition grounded in citations" },
                    { id: "unsupported", label: "Unsupported", desc: "Claims lack backing in text" },
                    { id: "hallucinated", label: "Hallucinated", desc: "Invented facts or fake citations" },
                    { id: "incomplete", label: "Incomplete", desc: "Key ingredients omitted" },
                    { id: "wrong_law", label: "Wrong Law", desc: "Repealed statute cited for post-July 2024" },
                  ].map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setLabel(item.id as any)}
                      className={`p-3 rounded-xl border text-left transition-all hover:scale-[1.01] shadow-3xs ${
                        label === item.id
                          ? "bg-[#071e17] text-white border-[#071e17]"
                          : "bg-white border-slate-300 text-slate-900 hover:bg-slate-50"
                      }`}
                    >
                      <div className="font-bold text-xs capitalize">{item.label}</div>
                      <div
                        className={`text-[11px] font-normal mt-0.5 leading-snug ${
                          label === item.id ? "text-slate-200" : "text-slate-600"
                        }`}
                      >
                        {item.desc}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Per-Claim Annotation */}
              <div>
                <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Atomic Proposition Scrutiny ({claims.length} claims)
                </label>
                <div className="space-y-3">
                  {claims.map((claim, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border transition-all space-y-2 ${
                        claim.is_supported
                          ? "bg-emerald-50/70 border-emerald-300"
                          : "bg-rose-50/70 border-rose-300"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm font-medium text-slate-900 leading-relaxed">
                          &ldquo;{claim.claim_text}&rdquo;
                        </p>
                        <button
                          type="button"
                          onClick={() => handleToggleClaim(idx)}
                          className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-all hover:scale-105 shrink-0 ${
                            claim.is_supported
                              ? "bg-emerald-200 text-emerald-950 border border-emerald-400"
                              : "bg-rose-200 text-rose-950 border border-rose-400"
                          }`}
                        >
                          {claim.is_supported ? (
                            <>
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              <span>Supported</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="h-3.5 w-3.5" />
                              <span>Unsupported</span>
                            </>
                          )}
                        </button>
                      </div>
                      <div className="flex items-center space-x-3 text-xs font-medium text-slate-600">
                        <span>Cited Paragraph: <b className="text-slate-900">¶ {claim.cited_para_no}</b></span>
                        <span>•</span>
                        <span>Audit Note: <i className="text-slate-700">{claim.notes}</i></span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Reviewer Free-Text Legal Notes */}
              <div>
                <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Reviewer Jurisprudential Analysis / Notes
                </label>
                <textarea
                  rows={4}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter detailed notes on ratio correctness, relevant landmark citations omitted, or transitional concordance issues..."
                  className="w-full text-sm font-medium text-slate-900 p-3.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0f2c24] leading-relaxed placeholder-slate-400"
                />
              </div>

              {/* Error Banner */}
              {error && (
                <div className="bg-rose-50 border border-rose-300 text-rose-950 rounded-xl p-3 text-sm font-semibold flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-rose-600" />
                  <span>{error}</span>
                </div>
              )}

              {/* Success Banner */}
              {submitted && (
                <div className="bg-emerald-50 border border-emerald-300 text-emerald-950 rounded-xl p-3 text-sm font-semibold flex items-center space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <span>Review submitted successfully! Gold dataset updated for evaluation.</span>
                </div>
              )}

              {/* Submit Button */}
              <div className="flex items-center justify-end pt-3 border-t border-slate-200">
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-[#071e17] hover:bg-[#0f2c24] text-white text-sm font-bold shadow-sm transition-shadow hover:shadow-md disabled:opacity-60 cursor-pointer"
                >
                  <span className="text-white font-bold">{submitting ? "Recording Label..." : "Submit Certified Evaluation"}</span>
                  <Send className="h-4 w-4 text-white" />
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Authorities Panel */}
        <RightAuthoritiesPanel />
      </div>
    </div>
  );
};

export default ReviewerPage;

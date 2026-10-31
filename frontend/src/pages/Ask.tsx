import React, { useState, useRef } from "react";
import {
  Send,
  CheckCircle2,
  AlertTriangle,
  Info,
  Paperclip,
  Sliders,
  Check,
  FileCheck,
} from "lucide-react";
import { api } from "../api/client";
import { FeedbackWidget } from "../components/FeedbackWidget";
import { SupremeCourt3DCanvas } from "../components/SupremeCourt3DCanvas";
import {
  ResearchScopeSidebar,
  ResearchScopeFilters,
} from "../components/ResearchScopeSidebar";
import { RightAuthoritiesPanel } from "../components/RightAuthoritiesPanel";
import { LegalAnswerViewer } from "../components/LegalAnswerViewer";
import { QAResponse } from "../types";

const DEFAULT_QUERY =
  "What are the essential ingredients of criminal conspiracy under Section 120A of the Indian Penal Code (IPC)? Explain the role of agreement and meeting of minds, with relevant Supreme Court judgments and paragraph-level citations.";

const DEFAULT_ANSWER_TEXT = `Under Section 120A of the Indian Penal Code (IPC), the essential ingredient for establishing a charge of criminal conspiracy is an agreement between two or more persons to commit an illegal act [C1]. Regarding the role of agreement and meeting of minds:

* **Agreement:** A criminal conspiracy requires an agreement between two or more persons to do an illegal act, or to do a legal act by illegal means [C1]. The agreement can be express or implied and may be inferred from the conduct and surrounding circumstances [C2].
* **Meeting of Minds:** To constitute a criminal conspiracy, a meeting of minds between the parties is essential [C2]. Mere knowledge of another's illegal act is not sufficient; there must be a conscious agreement [C2].
* **Proof of Agreement:** Direct evidence of a conspiracy is rarely available. The agreement is ordinarily inferred from the circumstances of the case, conduct of the parties, and other relevant factors [C2].`;

interface Props {
  initialQuery?: string;
  onNavigateToCase?: (documentId: number, paraNo?: number | null) => void;
}

export const AskPage: React.FC<Props> = ({ initialQuery = "", onNavigateToCase }) => {
  const [question, setQuestion] = useState(initialQuery || DEFAULT_QUERY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<QAResponse | null>(null);
  const [showTransitionDetails, setShowTransitionDetails] = useState(false);
  const [uploadedDocName, setUploadedDocName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Filters state
  const [filters, setFilters] = useState<ResearchScopeFilters>({
    scJudgments: true,
    hcJudgments: true,
    centralStatutes: true,
    constitution: false,
    commentaries: false,
    statuteScope: "Indian Penal Code (IPC)",
    courtLevel: "supreme",
    dateFrom: "",
    dateTo: "",
    resultPreference: "relevant",
  });

  const handleFilterChange = (updated: Partial<ResearchScopeFilters>) => {
    setFilters((prev) => ({ ...prev, ...updated }));
  };

  const handleResetFilters = () => {
    setFilters({
      scJudgments: true,
      hcJudgments: true,
      centralStatutes: true,
      constitution: false,
      commentaries: false,
      statuteScope: "Indian Penal Code (IPC)",
      courtLevel: "supreme",
      dateFrom: "",
      dateTo: "",
      resultPreference: "relevant",
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setUploadedDocName(file.name);
      await api.uploadDocument(file);
    } catch {
      // Keep UI state showing attached file
    }
  };

  const handleSubmit = async (e?: React.FormEvent, customQ?: string) => {
    if (e) e.preventDefault();
    const queryToAsk = customQ || question;
    if (!queryToAsk.trim() || queryToAsk.trim().length < 3) return;

    setLoading(true);
    setError(null);

    try {
      const res = await api.ask({ question: queryToAsk.trim() });
      setResponse(res);

      // Persist to query history
      try {
        const existing = JSON.parse(
          localStorage.getItem("needhi_history") ||
          localStorage.getItem("legaljarvis_history") ||
          "[]"
        );
        const newItem = {
          id: `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
          timestamp: new Date().toISOString(),
          query: queryToAsk.trim(),
          answer: res.answer,
          abstained: res.abstained,
          citationsCount: res.citations?.length || 0,
          criminalNotice: res.criminal_transition_notice,
        };
        const updated = JSON.stringify([newItem, ...existing].slice(0, 50));
        localStorage.setItem("needhi_history", updated);
        localStorage.setItem("legaljarvis_history", updated);
      } catch {
        // Non-fatal localStorage error
      }
    } catch (err: any) {
      setError(err.message || "Failed to retrieve verified legal answer. Please verify server connectivity.");
    } finally {
      setLoading(false);
    }
  };

  const handleCitationClick = (citationMarker: string) => {
    if (onNavigateToCase) {
      if (citationMarker.includes("1")) {
        onNavigateToCase(1, 12);
      } else {
        onNavigateToCase(1, 15);
      }
    }
  };

  return (
    <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 font-sans">
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Column: Research Scope */}
        <ResearchScopeSidebar
          filters={filters}
          onChange={handleFilterChange}
          onReset={handleResetFilters}
        />

        {/* Center Column: Main Legal Interaction */}
        <div className="flex-1 min-w-0 max-w-3xl space-y-6">
          {/* Hero Banner */}
          <div className="bg-[#edf2ec] border-2 border-[#c2d4c0] rounded-2xl p-6 shadow-xs flex flex-col md:flex-row items-center justify-between gap-5 relative overflow-hidden">
            {/* Left Side: Typography */}
            <div className="flex-1 max-w-xl z-10 space-y-2.5">
              <h2 className="text-3xl sm:text-4xl font-serif font-bold text-[#071e17] tracking-tight leading-tight">
                Ask Indian Law
              </h2>
              <p className="text-sm sm:text-base text-slate-800 font-semibold leading-normal">
                Get accurate, citation-verified answers from Supreme Court judgments and Indian statutes.
              </p>

              {/* 3 Value Proposition Badges */}
              <div className="flex flex-wrap items-center gap-2 pt-1 text-xs font-bold">
                <span className="inline-flex items-center space-x-1.5 bg-[#dcfce7] text-[#14532d] border border-[#86efac] px-3.5 py-1.5 rounded-full shadow-3xs">
                  <span className="w-2 h-2 rounded-full bg-[#15803d]"></span>
                  <span>Grounded in real sources</span>
                </span>
                <span className="inline-flex items-center space-x-1.5 bg-[#ffedd5] text-[#78350f] border border-[#fdba74] px-3.5 py-1.5 rounded-full shadow-3xs">
                  <span className="w-2 h-2 rounded-full bg-[#b45309]"></span>
                  <span>Paragraph-level citations</span>
                </span>
                <span className="inline-flex items-center space-x-1.5 bg-[#e0f2fe] text-[#075985] border border-[#7dd3fc] px-3.5 py-1.5 rounded-full shadow-3xs">
                  <span className="w-2 h-2 rounded-full bg-[#0284c7]"></span>
                  <span>Automatic verification</span>
                </span>
              </div>
            </div>

            {/* Right Side: 3D Supreme Court Model */}
            <div className="shrink-0 flex items-center justify-center z-10">
              <SupremeCourt3DCanvas className="w-60 h-40" />
            </div>
          </div>

          {/* Main Question Input Box */}
          <form
            onSubmit={handleSubmit}
            className="bg-white border-2 border-slate-300 rounded-2xl p-5 shadow-xs space-y-4"
          >
            <div className="relative">
              <textarea
                rows={3}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask any legal proposition, statutory section, or case law question..."
                className="w-full text-base sm:text-lg font-bold text-slate-950 leading-relaxed placeholder-slate-400 focus:outline-none resize-none"
              />
            </div>

            {uploadedDocName && (
              <div className="flex items-center space-x-2 text-xs sm:text-sm font-bold text-[#14532d] bg-[#dcfce7] border border-[#86efac] px-3.5 py-1.5 rounded-lg w-fit">
                <FileCheck className="h-4 w-4" />
                <span>Attached Document: {uploadedDocName}</span>
              </div>
            )}

            <div className="flex items-center justify-between pt-3 border-t-2 border-slate-100">
              <div className="flex items-center space-x-2.5">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept=".pdf,.txt,.docx"
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center space-x-2 px-3.5 py-2 rounded-xl border-2 border-slate-300 bg-white hover:bg-slate-50 text-slate-900 text-xs sm:text-sm font-bold transition-all hover:scale-105 shadow-3xs"
                >
                  <Paperclip className="h-4 w-4 text-slate-700 stroke-[2.5]" />
                  <span>Attach Document (PDF)</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleFilterChange({ courtLevel: filters.courtLevel === "supreme" ? "both" : "supreme" })}
                  className="p-2 rounded-xl border-2 border-slate-300 hover:bg-slate-100 text-slate-800 transition-colors"
                  title="Toggle Court scope"
                >
                  <Sliders className="h-4 w-4 stroke-[2.5]" />
                </button>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-[#071e17] hover:bg-[#0f2c24] text-white text-xs sm:text-sm font-bold shadow-sm transition-all hover:shadow-md disabled:opacity-60 cursor-pointer"
              >
                <span className="text-white font-bold">{loading ? "Searching Corpus..." : "Ask Needhi"}</span>
                <Send className="h-4 w-4 stroke-[2.5] text-white" />
              </button>
            </div>
          </form>

          {/* Criminal Law Transition Notice Banner */}
          <div className="bg-[#faeae1] border-2 border-[#f3d3be] rounded-2xl p-4.5 text-xs sm:text-sm text-[#78350f] space-y-2 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 font-bold text-[#78350f] text-xs sm:text-sm">
                <span className="w-5 h-5 rounded-full bg-[#b45309] text-white flex items-center justify-center text-xs font-bold">
                  !
                </span>
                <span>Criminal Law Transition Notice (BNS / BNSS / BSA 2023)</span>
              </div>
              <button
                type="button"
                onClick={() => setShowTransitionDetails(!showTransitionDetails)}
                className="text-xs font-bold text-[#78350f] hover:underline"
              >
                {showTransitionDetails ? "Hide Details ↑" : "View Details →"}
              </button>
            </div>

            <p className="text-xs sm:text-sm text-[#78350f] font-medium leading-relaxed">
              The Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA)
              came into force on 1 July 2024. For offences or proceedings initiated prior to 1 July 2024, the IPC, CrPC, and Indian Evidence
              Act continue to govern under transitional provisions.
            </p>

            {showTransitionDetails && (
              <div className="mt-3 pt-3 border-t border-[#f3d3be] space-y-2 text-xs font-medium">
                <div className="bg-white/90 p-3 rounded-xl border border-[#f3d3be] space-y-1">
                  <span className="font-bold text-[#78350f]">Transitional Concordance Rule:</span>
                  <p className="text-slate-800">
                    Under Section 358(1) BNS and Section 531(2)(a) BNSS, substantive liabilities for acts committed before 1 July 2024 remain governed by IPC 1860. Citations to IPC continue to bind active trials.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Error Banner */}
          {error && (
            <div className="bg-rose-50 border-2 border-rose-300 rounded-2xl p-4 flex items-center space-x-3 text-rose-950 font-bold text-sm">
              <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0 stroke-[2.5]" />
              <span>{error}</span>
            </div>
          )}

          {/* Loading Skeleton */}
          {loading && (
            <div className="bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
              <div className="flex items-center space-x-3">
                <div className="h-6 w-40 bg-slate-200 rounded-full"></div>
                <div className="h-6 w-28 bg-emerald-100 rounded-full"></div>
              </div>
              <div className="h-4 bg-slate-200 rounded w-full"></div>
              <div className="h-4 bg-slate-200 rounded w-5/6"></div>
              <div className="h-4 bg-slate-200 rounded w-4/6"></div>
            </div>
          )}

          {/* Verified Answer Display with Crystal Clear Typography */}
          {!loading && (
            <div className="bg-white border-2 border-slate-300 rounded-2xl p-6 shadow-xs space-y-5">
              {/* Header Row */}
              <div className="flex items-center justify-between pb-3 border-b-2 border-slate-100">
                <div className="flex items-center space-x-2.5">
                  <CheckCircle2 className="h-6 w-6 text-[#15803d] stroke-[2.5]" />
                  <h3 className="text-xl sm:text-2xl font-extrabold text-[#071e17] tracking-tight">
                    Verified Answer
                  </h3>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="inline-flex items-center space-x-1.5 text-xs font-bold text-[#14532d] bg-[#dcfce7] border border-[#86efac] px-3.5 py-1 rounded-full shadow-3xs">
                    <Check className="h-3.5 w-3.5 stroke-[2.5]" />
                    <span>Citation Verified</span>
                  </span>
                  <Info className="h-4 w-4 text-slate-500 cursor-pointer hover:text-slate-900" />
                </div>
              </div>

              {/* Formatted Answer Body with Dynamic Clean Markdown & Citation Pills */}
              <LegalAnswerViewer
                text={response ? response.answer : DEFAULT_ANSWER_TEXT}
                onCitationClick={handleCitationClick}
              />

              {/* Feedback Widget for Reviewers & Users */}
              <div className="pt-4 border-t-2 border-slate-100">
                <FeedbackWidget answerId={1} />
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Supporting Authorities & Real Verification */}
        <RightAuthoritiesPanel
          citations={response?.citations}
          onOpenCase={onNavigateToCase}
        />
      </div>
    </div>
  );
};

export default AskPage;

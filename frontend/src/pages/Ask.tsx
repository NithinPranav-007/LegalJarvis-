import React, { useState } from "react";
import {
  Send,
  HelpCircle,
  AlertOctagon,
  AlertCircle,
  BookOpen,
  ArrowRight,
  Sparkles,
  ExternalLink,
  RotateCcw,
} from "lucide-react";
import { api } from "../api/client";
import { FeedbackWidget } from "../components/FeedbackWidget";
import { LegalDisclaimer } from "../components/LegalDisclaimer";
import { TransitionNotice } from "../components/TransitionNotice";
import { QACitation, QAResponse } from "../types";

const SUGGESTED_QUESTIONS = [
  "What are the essential ingredients of criminal conspiracy under Section 120A IPC?",
  "What is the test for granting anticipatory bail under criminal jurisprudence?",
  "Is right to privacy recognized as a fundamental right under Article 21 of the Constitution?",
  "Can a suit for specific performance be decreed if the plaintiff was not ready and willing?",
];

interface Props {
  initialQuery?: string;
  onNavigateToCase?: (documentId: number, paraNo?: number | null) => void;
}

export const AskPage: React.FC<Props> = ({ initialQuery = "", onNavigateToCase }) => {
  const [question, setQuestion] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<QAResponse | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const handleSubmit = async (e?: React.FormEvent, customQ?: string) => {
    if (e) e.preventDefault();
    const queryToAsk = customQ || question;
    if (!queryToAsk.trim() || queryToAsk.trim().length < 3) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    setHasSubmitted(true);

    try {
      const res = await api.ask({ question: queryToAsk.trim() });
      setResponse(res);

      // Persist to local storage query history
      try {
        const existing = JSON.parse(localStorage.getItem("legaljarvis_history") || "[]");
        const newItem = {
          id: `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
          timestamp: new Date().toISOString(),
          query: queryToAsk.trim(),
          answer: res.answer,
          abstained: res.abstained,
          citationsCount: res.citations?.length || 0,
          criminalNotice: res.criminal_transition_notice,
        };
        localStorage.setItem("legaljarvis_history", JSON.stringify([newItem, ...existing].slice(0, 50)));
      } catch (err) {
        // Non-fatal localStorage error
      }
    } catch (err: any) {
      setError(err.message || "Failed to retrieve verified legal answer. Please verify connectivity.");
    } finally {
      setLoading(false);
    }
  };

  const handleCitationClick = (citation: QACitation) => {
    if (onNavigateToCase) {
      onNavigateToCase(citation.document_id, citation.para_no);
    }
  };

  // Helper to render answer text with clickable [C1], [C2] tags
  const renderFormattedAnswer = (text: string, citations: QACitation[]) => {
    if (!citations || citations.length === 0) return <p className="leading-relaxed">{text}</p>;

    // Regex to split on [C1], [C2], etc.
    const parts = text.split(/(\[C\d+\])/g);
    return (
      <p className="leading-relaxed whitespace-pre-line text-slate-800 font-serif text-base">
        {parts.map((part, idx) => {
          const match = part.match(/\[(C\d+)\]/);
          if (match) {
            const marker = `[${match[1]}]`;
            const citation = citations.find((c) => c.marker === marker);
            return (
              <button
                key={idx}
                type="button"
                onClick={() => citation && handleCitationClick(citation)}
                title={citation ? `${citation.title} (Para ${citation.para_no ?? "N/A"})` : "Citation"}
                className="inline-flex items-center text-xs font-mono font-bold bg-indigo-100 hover:bg-indigo-200 text-indigo-900 border border-indigo-300 rounded px-1.5 py-0.5 mx-0.5 cursor-pointer transition-colors"
              >
                {marker}
              </button>
            );
          }
          return <span key={idx}>{part}</span>;
        })}
      </p>
    );
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Intro Header */}
      <section className="mb-6 text-center">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">
          Citation-Verified Legal Q&amp;A
        </h2>
        <p className="text-slate-600 text-sm max-w-xl mx-auto">
          Ask Indian law questions grounded in Supreme Court and High Court precedents. Every claim is strictly
          verified against paragraph citations.
        </p>
      </section>

      {/* Query Input Box */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-300 overflow-hidden focus-within:ring-2 focus-within:ring-indigo-600 focus-within:border-transparent transition-all">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            placeholder="Ask a question on Indian case law, statutory interpretation, or constitutional principles..."
            className="w-full p-4 text-slate-900 placeholder-slate-400 focus:outline-none resize-none text-base"
          />
          <div className="bg-slate-50 px-4 py-2.5 flex items-center justify-between border-t border-slate-200">
            <span className="text-xs text-slate-500 flex items-center space-x-1">
              <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
              <span>Grounded in Supreme Court &amp; Central Statutes</span>
            </span>
            <button
              type="submit"
              disabled={loading || question.trim().length < 3}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-medium rounded-lg text-sm flex items-center space-x-1.5 transition-colors shadow-sm"
            >
              <span>{loading ? "Analyzing..." : "Ask LegalJarvis"}</span>
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </form>

      {/* Empty State */}
      {!hasSubmitted && !loading && !error && (
        <section aria-label="Suggested Questions" className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-indigo-700 mb-3">
            <HelpCircle className="h-5 w-5" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">Sample Indian Legal Inquiries</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {SUGGESTED_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuestion(q);
                  handleSubmit(undefined, q);
                }}
                className="text-left p-3.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-indigo-50/50 hover:border-indigo-200 text-slate-800 text-xs font-medium transition-colors flex items-start justify-between group"
              >
                <span>{q}</span>
                <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-indigo-600 flex-shrink-0 ml-2 mt-0.5" />
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Loading State */}
      {loading && (
        <div
          role="status"
          aria-live="polite"
          className="bg-white rounded-xl border border-slate-200 p-8 text-center shadow-sm space-y-4 my-6"
        >
          <div className="animate-spin h-9 w-9 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto" />
          <div>
            <h4 className="text-base font-semibold text-slate-800">Retrieving Authoritative Passages</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              Synthesizing legal reasoning, verifying paragraph references, and checking criminal law transition
              statutes...
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div
          role="alert"
          className="bg-red-50 border border-red-200 rounded-xl p-5 my-6 flex items-start space-x-3 text-red-900"
        >
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-bold text-red-800">Unable to Complete Request</h4>
            <p className="text-xs text-red-700 mt-1">{error}</p>
            <button
              type="button"
              onClick={() => handleSubmit()}
              className="mt-3 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-md flex items-center space-x-1.5 transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Retry Query</span>
            </button>
          </div>
        </div>
      )}

      {/* Abstain State */}
      {response && response.abstained && !loading && (
        <div
          role="alert"
          aria-label="Low Evidence Abstention"
          className="bg-amber-50 border border-amber-300 rounded-xl p-6 my-6 shadow-sm"
        >
          <div className="flex items-start space-x-3.5">
            <AlertOctagon className="h-6 w-6 text-amber-700 flex-shrink-0 mt-0.5" />
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-amber-800 block mb-1">
                Low-Evidence Abstention (Safety Protocol FR-03 / FR-06)
              </span>
              <h3 className="text-base font-bold text-amber-950 mb-2">
                LegalJarvis could not find sufficient authoritative Indian case law or statutory authority to reliably
                answer this question.
              </h3>
              <p className="text-xs text-amber-900 leading-relaxed mb-3">
                {response.abstention_reason ||
                  "Retrieved precedent passages did not meet the required citation support threshold (60%+ keyword support across verified judgments). To prevent legal hallucinations, LegalJarvis will not generate an unsubstantiated answer."}
              </p>
              <div className="bg-white/80 p-3 rounded border border-amber-200 text-xs text-amber-900">
                <span className="font-semibold block mb-1">Recommended Adjustments:</span>
                <ul className="list-disc list-inside space-y-1 text-slate-700">
                  <li>Check spelling of party names, Act names, or section numbers.</li>
                  <li>Inquire about established principles (e.g. anticipatory bail, mens rea, specific performance).</li>
                  <li>Verify if the question relates to state-specific local acts outside Supreme Court jurisdiction.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success State */}
      {response && !response.abstained && !loading && (
        <div className="space-y-6 my-6">
          {/* Criminal Transition Notice if triggered */}
          {response.criminal_transition_notice && (
            <TransitionNotice notice={response.criminal_transition_notice} />
          )}

          {/* Formatted Answer Container */}
          <article className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">Verified Answer</span>
              <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full font-medium">
                Citation Verified
              </span>
            </div>

            {renderFormattedAnswer(response.answer, response.citations)}

            {/* Inline Feedback Widget */}
            <FeedbackWidget query={response.question} />
          </article>

          {/* Supporting Citations Section */}
          {response.citations && response.citations.length > 0 && (
            <section aria-label="Authoritative Citations" className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                  Supporting Authorities ({response.citations.length})
                </h3>
                <span className="text-xs text-slate-500">Click marker or card to open Case Viewer</span>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {response.citations.map((c) => (
                  <div
                    key={c.marker}
                    onClick={() => handleCitationClick(c)}
                    className="bg-white border border-slate-200 hover:border-indigo-300 rounded-lg p-4 shadow-sm cursor-pointer transition-all hover:shadow"
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono font-bold bg-indigo-100 text-indigo-900 border border-indigo-300 rounded px-2 py-0.5">
                          {c.marker}
                        </span>
                        <h4 className="text-sm font-bold text-indigo-950 hover:text-indigo-600">{c.title}</h4>
                      </div>
                      <div className="flex items-center space-x-2 flex-shrink-0">
                        {c.para_no && (
                          <span className="text-xs bg-slate-100 text-slate-700 font-mono px-2 py-0.5 rounded">
                            Para {c.para_no}
                          </span>
                        )}
                        <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 text-xs text-slate-500 mb-2">
                      <span className="font-medium text-slate-700">{c.court}</span>
                      {c.neutral_citation && (
                        <>
                          <span>•</span>
                          <span className="font-mono">{c.neutral_citation}</span>
                        </>
                      )}
                    </div>

                    <p className="text-xs text-slate-700 bg-slate-50 p-2.5 rounded border border-slate-100 font-serif leading-relaxed">
                      &ldquo;{c.snippet}&rdquo;
                    </p>

                    <div className="mt-2 pt-2 border-t border-slate-100 text-[11px] text-slate-400 flex items-center justify-between">
                      <span className="truncate max-w-sm">{c.attribution}</span>
                      <span className="text-indigo-600 font-medium hover:underline flex items-center space-x-1">
                        <BookOpen className="h-3 w-3" />
                        <span>View Judgment</span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Legal Disclaimer */}
          <LegalDisclaimer />
        </div>
      )}
    </div>
  );
};

export default AskPage;

import React, { useState, useEffect } from "react";
import {
  Trash2,
  ArrowRight,
  Calendar,
  Search,
  CheckCircle2,
  AlertTriangle,
  SlidersHorizontal,
  Copy,
  Check,
  ShieldCheck,
} from "lucide-react";
import { SupremeCourt3DCanvas } from "../components/SupremeCourt3DCanvas";
import { Card3D } from "../components/Card3D";
import { RightAuthoritiesPanel } from "../components/RightAuthoritiesPanel";
import { LegalAnswerViewer } from "../components/LegalAnswerViewer";
import { HistoryItem } from "../types";

interface Props {
  onReAsk: (query: string) => void;
}

export const HistoryPage: React.FC<Props> = ({ onReAsk }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [filterText, setFilterText] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "verified" | "abstained">("all");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const loadHistory = () => {
    try {
      const stored = localStorage.getItem("needhi_history") || localStorage.getItem("legaljarvis_history");
      if (stored) {
        setHistory(JSON.parse(stored));
      } else {
        const initial: HistoryItem[] = [
          {
            id: "hist-default-1",
            timestamp: new Date().toISOString(),
            query:
              "What are the essential ingredients of criminal conspiracy under Section 120A of the Indian Penal Code (IPC)? Explain the role of agreement and meeting of minds, with relevant Supreme Court judgments and paragraph-level citations.",
            answer:
              "Under Section 120A of the Indian Penal Code (IPC), the essential ingredient for establishing a charge of criminal conspiracy is an agreement between two or more persons to commit an illegal act [C1]. Regarding the role of agreement and meeting of minds:\n\n* **Agreement:** A criminal conspiracy requires an agreement between two or more persons to do an illegal act, or to do a legal act by illegal means [C1]. The agreement can be express or implied and may be inferred from the conduct and surrounding circumstances [C2].\n* **Meeting of Minds:** To constitute a criminal conspiracy, a meeting of minds between the parties is essential [C2]. Mere knowledge of another's illegal act is not sufficient; there must be a conscious agreement [C2].\n* **Proof of Agreement:** Direct evidence of a conspiracy is rarely available. The agreement is ordinarily inferred from the circumstances of the case, conduct of the parties, and other relevant factors [C2].",
            abstained: false,
            citationsCount: 2,
            criminalNotice: "BNS S. 61 concordance applies.",
          },
          {
            id: "hist-default-2",
            timestamp: new Date(Date.now() - 3600000 * 4).toISOString(),
            query: "What is the test for granting anticipatory bail under Section 438 CrPC?",
            answer:
              "The Constitution Bench in Gurbaksh Singh Sibbia held that the power to grant anticipatory bail under Section 438 CrPC is of wide amplitude [C1]. The High Court or Court of Session must not impose unwarranted judicial conditions not contemplated by the statutory text [C2].",
            abstained: false,
            citationsCount: 2,
            criminalNotice: "BNSS S. 482 concordance applies.",
          },
        ];
        setHistory(initial);
        localStorage.setItem("needhi_history", JSON.stringify(initial));
        localStorage.setItem("legaljarvis_history", JSON.stringify(initial));
      }
    } catch {
      setHistory([]);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleClearHistory = () => {
    if (window.confirm("Are you sure you want to clear your local query history?")) {
      localStorage.removeItem("needhi_history");
      localStorage.removeItem("legaljarvis_history");
      setHistory([]);
    }
  };

  const copyAnswer = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredHistory = history.filter((item) => {
    if (statusFilter === "verified" && item.abstained) return false;
    if (statusFilter === "abstained" && !item.abstained) return false;
    if (filterText.trim()) {
      const queryMatch = item.query.toLowerCase().includes(filterText.toLowerCase());
      const answerMatch = item.answer.toLowerCase().includes(filterText.toLowerCase());
      return queryMatch || answerMatch;
    }
    return true;
  });

  return (
    <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 font-sans">
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Column: History Scope & Filter Sidebar */}
        <aside
          className="w-full lg:w-64 shrink-0 space-y-6 text-slate-900"
          aria-label="History Scope"
        >
          <div className="flex items-center justify-between pb-2 border-b border-slate-300">
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              History Scope
            </h2>
            <SlidersHorizontal className="h-4 w-4 text-slate-700" />
          </div>

          {/* Verification Status */}
          <div className="space-y-2.5">
            <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider">
              Verification Status
            </label>
            <div className="space-y-2 text-sm font-semibold">
              {[
                { id: "all", label: "All Past Queries" },
                { id: "verified", label: "Citation-Verified Only" },
                { id: "abstained", label: "Low-Evidence Abstained" },
              ].map((opt) => (
                <label key={opt.id} className="flex items-center space-x-2.5 cursor-pointer">
                  <input
                    type="radio"
                    name="statusFilter"
                    checked={statusFilter === opt.id}
                    onChange={() => setStatusFilter(opt.id as any)}
                    className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
                  />
                  <span className="text-slate-900">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Local Storage Privacy Note */}
          <div className="bg-[#edf2ec] border border-[#c2d4c0] rounded-xl p-4 text-xs text-slate-900 space-y-1.5 shadow-2xs">
            <div className="flex items-center space-x-2 font-bold text-slate-900">
              <ShieldCheck className="h-4 w-4 text-[#15803d]" />
              <span>Client-Side Privacy</span>
            </div>
            <p className="leading-relaxed text-slate-700 font-normal">
              All research history is stored locally in your browser. No queries or notes are logged to external telemetry.
            </p>
          </div>

          {/* Clear History Button */}
          {history.length > 0 && (
            <div className="pt-2">
              <button
                type="button"
                onClick={handleClearHistory}
                className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-800 text-xs font-bold border border-rose-300 transition-colors shadow-2xs"
              >
                <Trash2 className="h-4 w-4" />
                <span>Clear All History</span>
              </button>
            </div>
          )}
        </aside>

        {/* Center Column: Query Timeline & History List */}
        <div className="flex-1 min-w-0 max-w-3xl space-y-6">
          {/* Hero Banner with Side-by-Side 3D Canvas */}
          <div className="bg-[#edf2ec] border border-[#c2d4c0] rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-5 relative overflow-hidden">
            <div className="flex-1 max-w-xl z-10 space-y-2.5">
              <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#071e17] tracking-tight">
                Research Query History
              </h2>
              <p className="text-sm text-slate-700 font-medium leading-normal">
                Locally cached audit trail of queries, generated citations, and verification certificates.
              </p>

              <div className="flex flex-wrap items-center gap-2 pt-1 text-xs font-semibold">
                <span className="inline-flex items-center space-x-1.5 bg-[#dcfce7] text-[#14532d] border border-[#86efac] px-3 py-1 rounded-full shadow-3xs">
                  <span className="w-2 h-2 rounded-full bg-[#15803d]"></span>
                  <span>{history.length} Inquiries Logged</span>
                </span>
                <span className="inline-flex items-center space-x-1.5 bg-[#ffedd5] text-[#78350f] border border-[#fdba74] px-3 py-1 rounded-full shadow-3xs">
                  <span className="w-2 h-2 rounded-full bg-[#b45309]"></span>
                  <span>Local Browser Storage</span>
                </span>
              </div>
            </div>

            <div className="shrink-0 flex items-center justify-center z-10">
              <SupremeCourt3DCanvas className="w-60 h-40" />
            </div>
          </div>

          {/* History Search Bar */}
          <Card3D intensity={2} glare={true} className="rounded-2xl">
            <div className="bg-white border border-slate-300 rounded-2xl p-3.5 shadow-2xs">
              <div className="relative flex items-center">
                <Search className="absolute left-3.5 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                  placeholder="Search within past inquiries, topics, or answers..."
                  className="w-full pl-10 pr-4 py-1.5 text-sm font-medium text-slate-900 placeholder-slate-400 focus:outline-none"
                />
              </div>
            </div>
          </Card3D>

          {/* 3D History List */}
          <div className="space-y-4">
            {filteredHistory.map((item) => (
              <Card3D key={item.id} intensity={2} glare={false} className="rounded-2xl">
                <article className="bg-white border border-slate-300 rounded-2xl p-5 shadow-sm hover:border-slate-400 transition-all space-y-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1.5">
                      <h3 className="font-bold text-base sm:text-lg text-slate-950 leading-snug">
                        {item.query}
                      </h3>
                      <div className="flex items-center space-x-3 text-xs font-semibold text-slate-600">
                        <span className="flex items-center space-x-1">
                          <Calendar className="h-3.5 w-3.5 text-slate-500" />
                          <span>{new Date(item.timestamp).toLocaleString()}</span>
                        </span>
                        <span>•</span>
                        <span
                          className={`inline-flex items-center space-x-1 font-bold ${
                            item.abstained ? "text-amber-800" : "text-emerald-800"
                          }`}
                        >
                          {item.abstained ? (
                            <>
                              <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                              <span>Abstained (Low Confidence)</span>
                            </>
                          ) : (
                            <>
                              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                              <span>Citation Verified ({item.citationsCount} citations)</span>
                            </>
                          )}
                        </span>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => copyAnswer(item.id, item.answer)}
                      className="p-2 text-slate-400 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition shrink-0"
                      title="Copy Answer"
                    >
                      {copiedId === item.id ? (
                        <Check className="h-4 w-4 text-emerald-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </button>
                  </div>

                  {/* Clean Markdown & Citation Formatted Answer */}
                  <div className="bg-[#f8fafc] p-4 rounded-xl border border-slate-200 border-l-4 border-l-amber-500">
                    <LegalAnswerViewer
                      text={item.answer}
                      onCitationClick={() => onReAsk(item.query)}
                    />
                  </div>

                  {/* Card Footer Actions */}
                  <div className="pt-2 flex items-center justify-between border-t border-slate-200 text-xs font-semibold">
                    <span className="text-slate-600">
                      {item.criminalNotice ? "Transition concordance checked" : "General jurisprudence"}
                    </span>
                    <button
                      type="button"
                      onClick={() => onReAsk(item.query)}
                      className="flex items-center space-x-1.5 text-[#071e17] font-bold hover:underline"
                    >
                      <span>Re-Open Query in Ask Q&amp;A</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </article>
              </Card3D>
            ))}
          </div>

          {filteredHistory.length === 0 && (
            <Card3D intensity={2} glare={false} className="rounded-2xl">
              <div className="bg-white border border-slate-300 rounded-2xl p-10 text-center space-y-3">
                <p className="text-sm font-semibold text-slate-700">No past inquiries found matching your filters.</p>
              </div>
            </Card3D>
          )}
        </div>

        {/* Right Column: Authorities Panel */}
        <RightAuthoritiesPanel />
      </div>
    </div>
  );
};

export default HistoryPage;

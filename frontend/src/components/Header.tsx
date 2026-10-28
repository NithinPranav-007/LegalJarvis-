import React, { useState } from "react";
import {
  Scale,
  MessageSquareText,
  Search,
  BookOpen,
  History as HistoryIcon,
  ShieldCheck,
  ArrowRightLeft,
  X,
  ExternalLink,
} from "lucide-react";

export type NavTab = "ask" | "search" | "case" | "history" | "reviewer";

interface Props {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  userRole?: string;
}

const QUICK_CONCORDANCE = [
  { ipc: "Section 302 IPC", bns: "Section 103 BNS", label: "Murder & Capital Offences", note: "Section 103(2) adds explicit statutory offense for mob lynching / murder by group of 5+" },
  { ipc: "Section 304A IPC", bns: "Section 106 BNS", label: "Causing Death by Negligence", note: "Section 106(2) provides enhanced imprisonment for hit-and-run without reporting" },
  { ipc: "Section 420 IPC", bns: "Section 318(4) BNS", label: "Cheating & Dishonest Inducement", note: "Consolidated under Chapter XVIII on Offences Against Property" },
  { ipc: "Section 376 IPC", bns: "Section 64 BNS", label: "Rape & Aggravated Offences", note: "Restructured under Chapter V; enhanced minimum sentences & medical safeguards" },
  { ipc: "Section 124A IPC", bns: "Section 152 BNS", label: "Sedition -> Sovereignty / Integrity", note: "Colonial term 'Sedition' repealed; replaced by acts endangering sovereignty" },
  { ipc: "Section 498A IPC", bns: "Section 85 / 86 BNS", label: "Cruelty by Husband / Relatives", note: "Retained with codified bail and reconciliation guidelines" },
  { ipc: "Section 438 CrPC", bns: "Section 482 BNSS", label: "Direction for Grant of Anticipatory Bail", note: "Retains high court and sessions court jurisdiction with procedural clarity" },
];

export const Header: React.FC<Props> = ({ activeTab, onSelectTab, userRole = "researcher" }) => {
  const [showBridgeModal, setShowBridgeModal] = useState(false);
  const [searchFilter, setSearchFilter] = useState("");

  const filteredBridge = QUICK_CONCORDANCE.filter(
    (c) =>
      c.ipc.toLowerCase().includes(searchFilter.toLowerCase()) ||
      c.bns.toLowerCase().includes(searchFilter.toLowerCase()) ||
      c.label.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <>
      <header className="glass-nav border-b border-slate-200/80 sticky top-0 z-30 shadow-sm transition-all">
        <div className="max-w-6xl mx-auto px-4 py-3 flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Brand */}
          <div
            className="flex items-center space-x-3 cursor-pointer group"
            onClick={() => onSelectTab("ask")}
          >
            <div className="p-2 bg-gradient-to-br from-indigo-600 to-indigo-800 rounded-xl text-white shadow-sm shadow-indigo-200 group-hover:scale-105 transition-transform">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-black tracking-tight text-slate-900 group-hover:text-indigo-600 transition-colors">
                  LegalJarvis
                </h1>
                <span className="bg-indigo-100 text-indigo-900 border border-indigo-300 text-xs font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                  Indian Law
                </span>
                <span className="inline-flex items-center text-xs text-emerald-900 font-bold bg-emerald-100 border border-emerald-300 px-2 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mr-1.5 animate-pulse"></span>
                  SC Corpus Active
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">Citation-Verified Supreme Court &amp; High Court Intelligence</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav
            className="flex items-center space-x-1 bg-slate-100/80 p-1 rounded-xl border border-slate-200 text-xs font-medium"
            aria-label="Main Navigation"
          >
            <button
              type="button"
              onClick={() => onSelectTab("ask")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "ask"
                  ? "bg-white text-indigo-700 shadow-sm font-bold border border-slate-200/60"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              <MessageSquareText className="h-3.5 w-3.5" />
              <span>Ask Q&amp;A</span>
            </button>
            <button
              type="button"
              onClick={() => onSelectTab("search")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "search"
                  ? "bg-white text-indigo-700 shadow-sm font-bold border border-slate-200/60"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              <Search className="h-3.5 w-3.5" />
              <span>Search</span>
            </button>
            <button
              type="button"
              onClick={() => onSelectTab("case")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "case"
                  ? "bg-white text-indigo-700 shadow-sm font-bold border border-slate-200/60"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>Case Viewer</span>
            </button>
            <button
              type="button"
              onClick={() => onSelectTab("history")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "history"
                  ? "bg-white text-indigo-700 shadow-sm font-bold border border-slate-200/60"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              <HistoryIcon className="h-3.5 w-3.5" />
              <span>History</span>
            </button>
            <button
              type="button"
              onClick={() => onSelectTab("reviewer")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "reviewer"
                  ? "bg-white text-indigo-700 shadow-sm font-bold border border-slate-200/60"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Reviewer</span>
            </button>
          </nav>

          {/* Quick Bridge & User Role */}
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => setShowBridgeModal(true)}
              className="flex items-center space-x-1 text-xs bg-amber-100 hover:bg-amber-200 text-amber-950 border border-amber-300 px-2.5 py-1.5 rounded-lg font-bold transition-colors shadow-xs"
              title="Look up pre-2024 IPC/CrPC to 2024 BNS/BNSS statutory concordance"
            >
              <ArrowRightLeft className="h-3.5 w-3.5 text-amber-600" />
              <span className="hidden sm:inline">IPC ↔ BNS Bridge</span>
              <span className="sm:hidden">Bridge</span>
            </button>

            <div className="hidden sm:flex items-center space-x-1.5 text-xs bg-slate-50 border border-slate-200 px-2.5 py-1.5 rounded-lg text-slate-700 font-medium">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              <span className="capitalize">{userRole}</span>
            </div>
          </div>
        </div>
      </header>

      {/* IPC ↔ BNS Concordance Quick Lookup Modal */}
      {showBridgeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-2xl w-full p-6 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 bg-amber-100 text-amber-800 rounded-lg">
                  <ArrowRightLeft className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Indian Criminal Law Concordance Bridge
                  </h3>
                  <p className="text-xs text-slate-500">
                    Official gazette mapping between IPC (1860) / CrPC (1973) and BNS / BNSS (2023)
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowBridgeModal(false)}
                className="p-1 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4">
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Type section (e.g. 302, murder, 420, 376, bail)..."
                className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-xs placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-600 mb-3"
              />

              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {filteredBridge.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-white transition-all space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">
                        {item.ipc}
                      </span>
                      <ArrowRightLeft className="h-3.5 w-3.5 text-slate-400" />
                      <span className="font-bold text-xs text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-md">
                        {item.bns}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-slate-800 pt-1">{item.label}</div>
                    <p className="text-[11px] text-slate-600 leading-relaxed">{item.note}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>Section 358 BNS / 531 BNSS savings clause applies to pre-July 2024 acts.</span>
              <button
                type="button"
                onClick={() => setShowBridgeModal(false)}
                className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-medium hover:bg-slate-800 transition"
              >
                Close Bridge
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Header;

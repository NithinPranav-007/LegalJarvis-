import React, { useState } from "react";
import {
  MessageSquare,
  Search,
  BookOpen,
  History as HistoryIcon,
  ShieldCheck,
  ArrowRightLeft,
  X,
  Landmark,
  FileSignature,
} from "lucide-react";
import { Scales3DLogo } from "./Scales3DLogo";

export type NavTab = "ask" | "search" | "case" | "history" | "reviewer" | "petition";

interface Props {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  userRole?: string;
  userInitial?: string;
}

const QUICK_CONCORDANCE = [
  { ipc: "Section 120A IPC", bns: "Section 61 BNS", label: "Criminal Conspiracy", note: "Essential ingredient is agreement to commit illegal act. Agreement inferred from circumstances." },
  { ipc: "Section 302 IPC", bns: "Section 103 BNS", label: "Murder & Capital Offences", note: "Section 103(2) adds explicit statutory offense for mob lynching / murder by group of 5+" },
  { ipc: "Section 304A IPC", bns: "Section 106 BNS", label: "Causing Death by Negligence", note: "Section 106(2) provides enhanced imprisonment for hit-and-run without reporting" },
  { ipc: "Section 420 IPC", bns: "Section 318(4) BNS", label: "Cheating & Dishonest Inducement", note: "Consolidated under Chapter XVIII on Offences Against Property" },
  { ipc: "Section 376 IPC", bns: "Section 64 BNS", label: "Rape & Aggravated Offences", note: "Restructured under Chapter V; enhanced minimum sentences & medical safeguards" },
  { ipc: "Section 124A IPC", bns: "Section 152 BNS", label: "Sedition -> Sovereignty / Integrity", note: "Colonial term 'Sedition' repealed; replaced by acts endangering sovereignty" },
  { ipc: "Section 498A IPC", bns: "Section 85 / 86 BNS", label: "Cruelty by Husband / Relatives", note: "Retained with codified bail and reconciliation guidelines" },
  { ipc: "Section 438 CrPC", bns: "Section 482 BNSS", label: "Direction for Grant of Anticipatory Bail", note: "Retains high court and sessions court jurisdiction with procedural clarity" },
];

export const Header: React.FC<Props> = ({
  activeTab,
  onSelectTab,
  userRole = "Researcher",
  userInitial = "N",
}) => {
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
      <header className="bg-white border-b-2 border-slate-200/90 sticky top-0 z-30 shadow-xs">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          {/* Left: Brand with 3D Animated Scales Logo & Super Serif Typography */}
          <div
            className="flex items-center space-x-3.5 cursor-pointer shrink-0 group"
            onClick={() => onSelectTab("ask")}
          >
            <Scales3DLogo className="w-10 h-10" />
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl font-black text-[#071e17] tracking-tight leading-none group-hover:text-[#0f2c24] transition-colors">
                  Needhi
                </h1>
              </div>
              <p className="text-xs text-slate-700 font-bold tracking-tight mt-0.5">
                Citation-Verified Indian Law Intelligence
              </p>
            </div>
          </div>

          {/* Center: High Visibility Navigation Tabs */}
          <nav
            className="hidden md:flex items-center space-x-1.5 bg-slate-100/90 p-1.5 rounded-full border border-slate-300 text-sm font-bold"
            aria-label="Main Navigation"
          >
            <button
              type="button"
              onClick={() => onSelectTab("ask")}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-full transition-all ${
                activeTab === "ask"
                  ? "bg-white text-[#071e17] shadow-sm font-black border border-slate-200"
                  : "text-slate-700 hover:text-slate-950 hover:bg-slate-200/60"
              }`}
            >
              <MessageSquare className="h-4 w-4 stroke-[2.5]" />
              <span>Ask Q&amp;A</span>
            </button>

            <button
              type="button"
              onClick={() => onSelectTab("search")}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-full transition-all ${
                activeTab === "search"
                  ? "bg-white text-[#071e17] shadow-sm font-black border border-slate-200"
                  : "text-slate-700 hover:text-slate-950 hover:bg-slate-200/60"
              }`}
            >
              <Search className="h-4 w-4 stroke-[2.5]" />
              <span>Search</span>
            </button>

            <button
              type="button"
              onClick={() => onSelectTab("case")}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-full transition-all ${
                activeTab === "case"
                  ? "bg-white text-[#071e17] shadow-sm font-black border border-slate-200"
                  : "text-slate-700 hover:text-slate-950 hover:bg-slate-200/60"
              }`}
            >
              <BookOpen className="h-4 w-4 stroke-[2.5]" />
              <span>Case Viewer</span>
            </button>

            <button
              type="button"
              onClick={() => onSelectTab("history")}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-full transition-all ${
                activeTab === "history"
                  ? "bg-white text-[#071e17] shadow-sm font-black border border-slate-200"
                  : "text-slate-700 hover:text-slate-950 hover:bg-slate-200/60"
              }`}
            >
              <HistoryIcon className="h-4 w-4 stroke-[2.5]" />
              <span>History</span>
            </button>

            <button
              type="button"
              onClick={() => onSelectTab("reviewer")}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-full transition-all ${
                activeTab === "reviewer"
                  ? "bg-white text-[#071e17] shadow-sm font-black border border-slate-200"
                  : "text-slate-700 hover:text-slate-950 hover:bg-slate-200/60"
              }`}
            >
              <ShieldCheck className="h-4 w-4 stroke-[2.5]" />
              <span>Reviewer</span>
            </button>

            <button
              type="button"
              onClick={() => onSelectTab("petition")}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-full transition-all ${
                activeTab === "petition"
                  ? "bg-white text-[#071e17] shadow-sm font-black border border-slate-200"
                  : "text-slate-700 hover:text-slate-950 hover:bg-slate-200/60"
              }`}
            >
              <FileSignature className="h-4 w-4 stroke-[2.5]" />
              <span>Petition Generator</span>
            </button>
          </nav>

          {/* Right: Quick Concordance Bridge & User Avatar */}
          <div className="flex items-center space-x-3 shrink-0">
            {/* IPC <-> BNS Bridge Pill Button */}
            <button
              type="button"
              onClick={() => setShowBridgeModal(true)}
              className="flex items-center space-x-2 bg-[#faeae1] hover:bg-[#f5ddcc] text-[#78350f] border-2 border-[#f3d3be] px-4 py-1.5 rounded-full text-xs sm:text-sm font-black transition-all hover:scale-105 shadow-xs"
              title="Look up pre-2024 IPC/CrPC to 2024 BNS/BNSS statutory concordance"
            >
              <ArrowRightLeft className="h-4 w-4 text-[#b45309] stroke-[2.5]" />
              <span className="hidden sm:inline">IPC ↔ BNS Bridge</span>
              <span className="sm:hidden">Bridge</span>
            </button>

            <div className="h-5 w-[1.5px] bg-slate-300 hidden sm:block" />

            {/* Researcher Pill */}
            <div className="hidden sm:flex items-center space-x-2 bg-[#e6f4ea] text-[#14532d] border-2 border-[#86efac] px-4 py-1.5 rounded-full text-xs sm:text-sm font-black shadow-2xs">
              <Landmark className="h-4 w-4 text-[#15803d] stroke-[2.5]" />
              <span>{userRole}</span>
            </div>

            {/* User Avatar Circle */}
            <div
              className="w-8 h-8 rounded-full bg-[#0a231c] text-white font-black text-sm flex items-center justify-center shadow-xs cursor-pointer hover:scale-110 transition-transform"
              title={`Active User: ${userInitial}`}
            >
              {userInitial}
            </div>
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <div className="flex md:hidden overflow-x-auto px-4 py-2 border-t border-slate-200 bg-slate-50 gap-2 text-xs font-bold">
          <button
            type="button"
            onClick={() => onSelectTab("ask")}
            className={`px-3.5 py-1.5 rounded-full whitespace-nowrap ${
              activeTab === "ask" ? "bg-white text-slate-950 font-black shadow-xs border border-slate-300" : "text-slate-700"
            }`}
          >
            Ask Q&amp;A
          </button>
          <button
            type="button"
            onClick={() => onSelectTab("search")}
            className={`px-3.5 py-1.5 rounded-full whitespace-nowrap ${
              activeTab === "search" ? "bg-white text-slate-950 font-black shadow-xs border border-slate-300" : "text-slate-700"
            }`}
          >
            Search
          </button>
          <button
            type="button"
            onClick={() => onSelectTab("case")}
            className={`px-3.5 py-1.5 rounded-full whitespace-nowrap ${
              activeTab === "case" ? "bg-white text-slate-950 font-black shadow-xs border border-slate-300" : "text-slate-700"
            }`}
          >
            Case Viewer
          </button>
          <button
            type="button"
            onClick={() => onSelectTab("history")}
            className={`px-3.5 py-1.5 rounded-full whitespace-nowrap ${
              activeTab === "history" ? "bg-white text-slate-950 font-black shadow-xs border border-slate-300" : "text-slate-700"
            }`}
          >
            History
          </button>
          <button
            type="button"
            onClick={() => onSelectTab("reviewer")}
            className={`px-3.5 py-1.5 rounded-full whitespace-nowrap ${
              activeTab === "reviewer" ? "bg-white text-slate-950 font-black shadow-xs border border-slate-300" : "text-slate-700"
            }`}
          >
            Reviewer
          </button>
          <button
            type="button"
            onClick={() => onSelectTab("petition")}
            className={`px-3.5 py-1.5 rounded-full whitespace-nowrap ${
              activeTab === "petition" ? "bg-white text-slate-950 font-black shadow-xs border border-slate-300" : "text-slate-700"
            }`}
          >
            Petition Generator
          </button>
        </div>
      </header>

      {/* IPC ↔ BNS Concordance Quick Lookup Modal */}
      {showBridgeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/50 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl shadow-2xl border-2 border-slate-300 max-w-2xl w-full p-6 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-[#faeae1] text-[#78350f] rounded-xl border-2 border-[#f3d3be]">
                  <ArrowRightLeft className="h-5 w-5 stroke-[2.5]" />
                </div>
                <div>
                  <h3 className="text-lg font-serif font-black text-slate-950">
                    Indian Criminal Law Concordance Bridge
                  </h3>
                  <p className="text-xs text-slate-700 font-bold">
                    Official gazette mapping between IPC (1860) / CrPC (1973) and BNS / BNSS (2023)
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowBridgeModal(false)}
                className="p-2 text-slate-500 hover:text-slate-950 rounded-lg hover:bg-slate-100 transition"
                aria-label="Close"
              >
                <X className="h-5 w-5 stroke-[2.5]" />
              </button>
            </div>

            <div className="mt-4">
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Type section (e.g. 120A, 302, murder, 420, bail)..."
                className="w-full px-4 py-3 border-2 border-slate-300 rounded-xl text-sm font-bold placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0f2c24] mb-3 text-slate-950"
              />

              <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                {filteredBridge.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border-2 border-slate-200 bg-[#f9faf8] hover:bg-white hover:border-slate-400 transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-black text-xs text-[#78350f] bg-[#faeae1] border border-[#f3d3be] px-3 py-1 rounded-md">
                        {item.ipc}
                      </span>
                      <ArrowRightLeft className="h-4 w-4 text-slate-500 stroke-[2.5]" />
                      <span className="font-mono font-black text-xs text-[#14532d] bg-[#e6f4ea] border border-[#bbf7d0] px-3 py-1 rounded-md">
                        {item.bns}
                      </span>
                    </div>
                    <div className="text-sm font-black text-slate-950 pt-0.5">{item.label}</div>
                    <p className="text-xs text-slate-800 font-medium leading-relaxed">{item.note}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-700 font-bold">
              <span>Section 358 BNS / 531 BNSS savings clause applies to pre-July 2024 acts.</span>
              <button
                type="button"
                onClick={() => setShowBridgeModal(false)}
                className="px-5 py-2 bg-[#0a231c] text-white rounded-xl text-xs font-black hover:bg-[#163f34] transition shadow-xs"
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

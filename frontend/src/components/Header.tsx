import React from "react";
import { Scale, MessageSquareText, Search, BookOpen, History as HistoryIcon, ShieldCheck } from "lucide-react";

export type NavTab = "ask" | "search" | "case" | "history" | "reviewer";

interface Props {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  userRole?: string;
}

export const Header: React.FC<Props> = ({ activeTab, onSelectTab, userRole = "researcher" }) => {
  return (
    <header className="border-b bg-white border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 py-3 flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onSelectTab("ask")}>
          <div className="p-2 bg-indigo-50 border border-indigo-100 rounded-lg text-indigo-700">
            <Scale className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">LegalJarvis</h1>
              <span className="bg-indigo-100 text-indigo-800 text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider">
                Indian Law
              </span>
            </div>
            <p className="text-xs text-slate-500">Citation-Verified Supreme Court & High Court Intelligence</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-medium" aria-label="Main Navigation">
          <button
            type="button"
            onClick={() => onSelectTab("ask")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "ask"
                ? "bg-white text-indigo-700 shadow-sm font-semibold"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
            }`}
          >
            <MessageSquareText className="h-3.5 w-3.5" />
            <span>Ask Q&amp;A</span>
          </button>
          <button
            type="button"
            onClick={() => onSelectTab("search")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "search"
                ? "bg-white text-indigo-700 shadow-sm font-semibold"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
            }`}
          >
            <Search className="h-3.5 w-3.5" />
            <span>Search</span>
          </button>
          <button
            type="button"
            onClick={() => onSelectTab("case")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "case"
                ? "bg-white text-indigo-700 shadow-sm font-semibold"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
            }`}
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span>Case Viewer</span>
          </button>
          <button
            type="button"
            onClick={() => onSelectTab("history")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "history"
                ? "bg-white text-indigo-700 shadow-sm font-semibold"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
            }`}
          >
            <HistoryIcon className="h-3.5 w-3.5" />
            <span>History</span>
          </button>
          <button
            type="button"
            onClick={() => onSelectTab("reviewer")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "reviewer"
                ? "bg-white text-indigo-700 shadow-sm font-semibold"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
            }`}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Reviewer</span>
          </button>
        </nav>

        {/* User Role Badge */}
        <div className="hidden sm:flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 text-xs bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-md text-slate-700">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span className="capitalize">{userRole}</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

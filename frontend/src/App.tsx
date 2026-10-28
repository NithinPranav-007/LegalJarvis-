import React, { useState } from "react";
import { Header, NavTab } from "./components/Header";
import { LegalDisclaimer } from "./components/LegalDisclaimer";
import { AskPage } from "./pages/Ask";
import { CaseViewerPage } from "./pages/CaseViewer";
import { HistoryPage } from "./pages/History";
import { ReviewerPage } from "./pages/Reviewer";
import { SearchPage } from "./pages/Search";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>("ask");
  const [selectedDocId, setSelectedDocId] = useState<number>(1);
  const [highlightParaNo, setHighlightParaNo] = useState<number | null>(null);
  const [askQuery, setAskQuery] = useState<string>("");

  const navigateToCase = (documentId: number, paraNo?: number | null) => {
    setSelectedDocId(documentId);
    setHighlightParaNo(paraNo ?? null);
    setActiveTab("case");
  };

  const handleReAsk = (query: string) => {
    setAskQuery(query);
    setActiveTab("ask");
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col justify-between">
      <div>
        <Header activeTab={activeTab} onSelectTab={setActiveTab} />

        <main id="main-content">
          {activeTab === "ask" && (
            <AskPage
              key={askQuery}
              initialQuery={askQuery}
              onNavigateToCase={navigateToCase}
            />
          )}

          {activeTab === "search" && (
            <SearchPage onNavigateToCase={navigateToCase} />
          )}

          {activeTab === "case" && (
            <CaseViewerPage
              documentId={selectedDocId}
              highlightParaNo={highlightParaNo}
              onSelectDocument={(id) => {
                setSelectedDocId(id);
                setHighlightParaNo(null);
              }}
            />
          )}

          {activeTab === "history" && (
            <HistoryPage onReAsk={handleReAsk} />
          )}

          {activeTab === "reviewer" && (
            <ReviewerPage />
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 mt-12 text-slate-500 text-xs">
        <div className="max-w-6xl mx-auto px-4 space-y-4">
          <LegalDisclaimer />
          <div className="flex flex-col sm:flex-row items-center justify-between pt-2 border-t border-slate-100 text-[11px] gap-2">
            <span>
              LegalJarvis AI &copy; {new Date().getFullYear()} — Grounded Supreme Court of India Research System.
            </span>
            <span>
              Open Government Data (OGD) / Creative Commons Attribution (CC-BY 4.0).
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;

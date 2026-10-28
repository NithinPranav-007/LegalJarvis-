import React, { useState, useEffect } from "react";
import { History as HistoryIcon, Trash2, ArrowRight, Calendar, Search, AlertOctagon, Info } from "lucide-react";
import { HistoryItem } from "../types";

interface Props {
  onReAsk: (query: string) => void;
}

export const HistoryPage: React.FC<Props> = ({ onReAsk }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [filterText, setFilterText] = useState("");

  const loadHistory = () => {
    try {
      const stored = localStorage.getItem("legaljarvis_history");
      if (stored) {
        setHistory(JSON.parse(stored));
      } else {
        setHistory([]);
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
      localStorage.removeItem("legaljarvis_history");
      setHistory([]);
    }
  };

  const filteredHistory = history.filter(
    (item) =>
      item.query.toLowerCase().includes(filterText.toLowerCase()) ||
      item.answer.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-6 border-b border-slate-200 gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-50 border border-indigo-100 rounded-lg text-indigo-700">
            <HistoryIcon className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Research Query History</h2>
            <p className="text-xs text-slate-500">Session and past inquiries stored in local storage</p>
          </div>
        </div>

        {history.length > 0 && (
          <button
            type="button"
            onClick={handleClearHistory}
            className="px-3 py-1.5 border border-slate-300 hover:border-rose-400 hover:bg-rose-50 text-slate-600 hover:text-rose-700 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition-colors self-start sm:self-auto"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Filter input */}
      {history.length > 0 && (
        <div className="relative mb-6">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Filter past inquiries or answers..."
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-600"
          />
        </div>
      )}

      {/* Empty State */}
      {history.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <HistoryIcon className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No Query History Yet</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Questions you submit on the Ask page will automatically appear here for review and quick re-inquiry.
          </p>
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-xs">
          No previous inquiries match &ldquo;{filterText}&rdquo;.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredHistory.map((item) => (
            <article
              key={item.id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:border-indigo-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-4 mb-2">
                <h3 className="text-sm font-bold text-slate-900 leading-snug">{item.query}</h3>
                <button
                  type="button"
                  onClick={() => onReAsk(item.query)}
                  className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-md text-xs font-semibold flex items-center space-x-1 flex-shrink-0 transition-colors"
                >
                  <span>Re-Ask</span>
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>

              <div className="flex items-center space-x-3 text-[11px] text-slate-400 mb-3">
                <span className="flex items-center space-x-1">
                  <Calendar className="h-3 w-3" />
                  <span>{new Date(item.timestamp).toLocaleString()}</span>
                </span>
                <span>•</span>
                <span>{item.citationsCount} citations referenced</span>
                {item.abstained && (
                  <>
                    <span>•</span>
                    <span className="text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded font-semibold flex items-center space-x-1">
                      <AlertOctagon className="h-3 w-3" />
                      <span>Abstained</span>
                    </span>
                  </>
                )}
                {item.criminalNotice && (
                  <>
                    <span>•</span>
                    <span className="text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded font-semibold flex items-center space-x-1">
                      <Info className="h-3 w-3" />
                      <span>Transition Notice</span>
                    </span>
                  </>
                )}
              </div>

              <p className="text-xs text-slate-700 line-clamp-3 bg-slate-50 p-3 rounded border border-slate-100 font-serif leading-relaxed">
                {item.answer}
              </p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoryPage;

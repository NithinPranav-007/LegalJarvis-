import React, { useState } from "react";
import {
  Search as SearchIcon,
  BookOpen,
  AlertCircle,
  ExternalLink,
  Sparkles,
  Layers,
  Calendar,
  Building,
  Copy,
  Check,
} from "lucide-react";
import { api } from "../api/client";
import { SearchItem } from "../types";

const FEATURED_SEARCHES = [
  { label: "Right to Privacy (Puttaswamy)", query: "right to privacy fundamental right Article 21" },
  { label: "Section 302 IPC Murder / 103 BNS", query: "Section 302 IPC murder ingredients intention knowledge" },
  { label: "Anticipatory Bail (CrPC 438)", query: "anticipatory bail discretion Section 438 CrPC" },
  { label: "Decriminalization S. 377 (Navtej)", query: "Section 377 IPC constitutional validity Navtej Johar" },
  { label: "Triple Talaq (Shayara Bano)", query: "talaq-e-biddat arbitrary constitutional Shayara Bano" },
];

interface Props {
  onNavigateToCase?: (documentId: number, paraNo?: number | null) => void;
}

export const SearchPage: React.FC<Props> = ({ onNavigateToCase }) => {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"hybrid" | "lexical" | "dense">("hybrid");
  const [results, setResults] = useState<SearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [copiedCitation, setCopiedCitation] = useState<string | null>(null);

  const executeSearch = async (searchTerm: string, searchMode: "hybrid" | "lexical" | "dense") => {
    if (!searchTerm.trim() || searchTerm.length < 2) return;

    setLoading(true);
    setError(null);
    try {
      const data = await api.search({
        query: searchTerm.trim(),
        mode: searchMode,
        limit: 20,
      });
      setResults(data.results || []);
      setHasSearched(true);
    } catch (err: any) {
      setError(err.message || "An error occurred while connecting to LegalJarvis search.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(query, mode);
  };

  const handleQuickChip = (chipQuery: string) => {
    setQuery(chipQuery);
    executeSearch(chipQuery, mode);
  };

  const handleSelectHit = (item: SearchItem) => {
    if (onNavigateToCase) {
      onNavigateToCase(item.document_id, item.para_no);
    }
  };

  const copyCitation = (e: React.MouseEvent, citation: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(citation);
    setCopiedCitation(citation);
    setTimeout(() => setCopiedCitation(null), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Search Header */}
      <section className="mb-6 text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-indigo-100 border border-indigo-300 text-indigo-900 text-xs font-bold mb-3">
          <Sparkles className="h-3.5 w-3.5 text-indigo-700" />
          <span>Supreme Court of India • Open Precedent Corpus</span>
        </div>
        <h2 className="text-3xl font-black text-slate-900 tracking-tight mb-2">
          Indian Case Law &amp; Precedent Search
        </h2>
        <p className="text-slate-700 text-sm leading-relaxed">
          Search authoritative judgments using Reciprocal Rank Fusion combining BM25 lexical precision and BGE-M3 dense embeddings.
        </p>
      </section>

      {/* Quick Search Chips */}
      <div className="mb-4 flex flex-wrap items-center justify-center gap-1.5 text-xs">
        <span className="text-slate-600 font-bold mr-1 flex items-center">
          <Layers className="h-3 w-3 mr-1" /> Landmark:
        </span>
        {FEATURED_SEARCHES.map((chip, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleQuickChip(chip.query)}
            className="px-2.5 py-1 rounded-full bg-white hover:bg-indigo-50 border border-slate-300 hover:border-indigo-400 text-slate-800 hover:text-indigo-900 font-semibold transition-all shadow-2xs hover:scale-102"
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-6 space-y-3">
        <div className="relative flex items-center shadow-sm">
          <SearchIcon className="absolute left-4 h-5 w-5 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. right to privacy, specific performance, section 302 IPC..."
            className="w-full pl-12 pr-32 py-3.5 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent text-base font-normal transition-all"
          />
          <button
            type="submit"
            disabled={loading || query.trim().length < 2}
            className="absolute right-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-semibold rounded-lg text-sm transition-all shadow-xs flex items-center space-x-1.5"
          >
            {loading ? (
              <>
                <div className="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Searching...</span>
              </>
            ) : (
              <span>Search</span>
            )}
          </button>
        </div>

        {/* Retrieval Mode selector */}
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs pt-1">
          <div className="flex items-center space-x-1.5">
            <span className="font-semibold text-slate-700">Retrieval Mode:</span>
            {(
              [
                ["hybrid", "Hybrid (BM25 + Dense + Reranker)"],
                ["dense", "Dense (BGE-M3 Embeddings)"],
                ["lexical", "Lexical (BM25 / FTS)"],
              ] as const
            ).map(([val, label]) => (
              <button
                key={val}
                type="button"
                onClick={() => {
                  setMode(val);
                  if (query.trim().length >= 2) executeSearch(query, val);
                }}
                className={`px-2.5 py-1 rounded-lg border transition-all ${
                  mode === val
                    ? "bg-indigo-50 border-indigo-300 text-indigo-700 font-bold shadow-2xs"
                    : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <span className="text-xs text-slate-600 font-medium">
            Grounding threshold: 60%+ support
          </span>
        </div>
      </form>

      {/* Error Notice */}
      {error && (
        <div role="alert" className="mb-6 p-4 bg-red-50 border border-red-200 text-red-800 rounded-xl flex items-start space-x-3 text-sm">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {hasSearched && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-500 pb-2 border-b border-slate-200">
            <span className="font-medium">Found <strong className="text-slate-800 font-bold">{results.length}</strong> authoritative results for &ldquo;{query}&rdquo;</span>
            <span className="capitalize font-mono bg-slate-100 px-2 py-0.5 rounded text-[11px]">Mode: {mode} Relevance</span>
          </div>

          {results.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
              <BookOpen className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">No matching judgments found</h3>
              <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
                Try searching with broader terms or check spelling of parties or statute provisions.
              </p>
            </div>
          ) : (
            results.map((item) => (
              <article
                key={item.chunk_id}
                onClick={() => handleSelectHit(item)}
                className="legal-card p-5 group cursor-pointer hover:border-indigo-400"
              >
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors flex items-center space-x-1.5">
                      <span>{item.title}</span>
                      <ExternalLink className="h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-indigo-600" />
                    </h3>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {item.para_no && (
                      <span className="bg-slate-100 text-slate-700 text-xs px-2.5 py-0.5 rounded-md font-mono font-bold">
                        Para {item.para_no}
                      </span>
                    )}
                    {item.segment_type && (
                      <span className="bg-indigo-50 border border-indigo-200/60 text-indigo-700 text-xs px-2.5 py-0.5 rounded-md uppercase tracking-wider font-bold">
                        {item.segment_type}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mb-3">
                  <span className="font-semibold text-slate-700 flex items-center">
                    <Building className="h-3 w-3 mr-1 text-slate-400" />
                    {item.court}
                  </span>
                  {item.neutral_citation && (
                    <span className="inline-flex items-center font-mono bg-slate-100 border border-slate-200/80 px-2 py-0.5 rounded text-[11px] text-slate-700">
                      {item.neutral_citation}
                      <button
                        type="button"
                        onClick={(e) => copyCitation(e, item.neutral_citation!)}
                        className="ml-1 text-slate-400 hover:text-slate-700 p-0.5"
                        title="Copy neutral citation"
                      >
                        {copiedCitation === item.neutral_citation ? (
                          <Check className="h-2.5 w-2.5 text-emerald-600" />
                        ) : (
                          <Copy className="h-2.5 w-2.5" />
                        )}
                      </button>
                    </span>
                  )}
                  {item.decision_date && (
                    <span className="flex items-center text-slate-500 text-[11px]">
                      <Calendar className="h-3 w-3 mr-1 text-slate-400" />
                      {item.decision_date}
                    </span>
                  )}
                </div>

                <p className="text-sm text-slate-700 leading-relaxed bg-slate-50/80 p-3.5 rounded-xl border border-slate-200/60 font-serif">
                  {item.snippet}
                </p>

                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-slate-500 font-medium">Relevance Score: {item.score.toFixed(4)}</span>
                  </div>
                  <span className="truncate max-w-md text-[11px]">{item.attribution}</span>
                </div>
              </article>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default SearchPage;

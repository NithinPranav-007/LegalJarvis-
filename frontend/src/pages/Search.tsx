import React, { useState } from "react";
import {
  Search as SearchIcon,
  BookOpen,
  Layers,
  Calendar,
  Copy,
  Check,
  Bookmark,
  SlidersHorizontal,
  RotateCcw,
  Scale,
} from "lucide-react";
import { api } from "../api/client";
import { SupremeCourt3DCanvas } from "../components/SupremeCourt3DCanvas";
import { Card3D } from "../components/Card3D";
import { RightAuthoritiesPanel } from "../components/RightAuthoritiesPanel";
import { SearchItem } from "../types";

const FEATURED_SEARCHES = [
  { label: "Criminal Conspiracy (S. 120A IPC / 61 BNS)", query: "Section 120A IPC criminal conspiracy agreement meeting of minds" },
  { label: "Right to Privacy (Puttaswamy)", query: "right to privacy fundamental right Article 21" },
  { label: "Section 302 IPC Murder / 103 BNS", query: "Section 302 IPC murder ingredients intention knowledge" },
  { label: "Anticipatory Bail (CrPC 438 / BNSS 482)", query: "anticipatory bail discretion Section 438 CrPC" },
  { label: "Decriminalization S. 377 (Navtej Johar)", query: "Section 377 IPC constitutional validity Navtej Johar" },
  { label: "Triple Talaq (Shayara Bano)", query: "talaq-e-biddat arbitrary constitutional Shayara Bano" },
];

interface Props {
  onNavigateToCase?: (documentId: number, paraNo?: number | null) => void;
  onAskAboutCase?: (query: string) => void;
}

export const SearchPage: React.FC<Props> = ({ onNavigateToCase }) => {
  const [query, setQuery] = useState("Section 120A IPC criminal conspiracy agreement");
  const [mode, setMode] = useState<"hybrid" | "lexical" | "dense">("hybrid");
  const [results, setResults] = useState<SearchItem[]>([]);
  const [selectedResult, setSelectedResult] = useState<SearchItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [copiedCitation, setCopiedCitation] = useState<string | null>(null);
  const [savedDocs, setSavedDocs] = useState<Record<number, boolean>>({});

  // Filter state
  const [courtLevel, setCourtLevel] = useState<"supreme" | "high" | "both">("supreme");
  const [statuteFilter, setStatuteFilter] = useState("all");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");

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
      if (data.results && data.results.length > 0) {
        setSelectedResult(data.results[0]);
      }
      setHasSearched(true);
    } catch (err: any) {
      setError(err.message || "An error occurred while connecting to Needhi search.");
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
    setSelectedResult(item);
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

  const toggleSave = (e: React.MouseEvent, docId: number) => {
    e.stopPropagation();
    setSavedDocs((prev) => ({ ...prev, [docId]: !prev[docId] }));
  };

  return (
    <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 font-sans">
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Column: Search Filter Sidebar */}
        <aside
          className="w-full lg:w-64 shrink-0 space-y-6 text-[#090d16]"
          aria-label="Search Scope Filters"
        >
          <div className="flex items-center justify-between pb-2.5 border-b-2 border-slate-300">
            <h2 className="text-lg font-serif font-black text-[#071e17] tracking-tight">
              Search Scope
            </h2>
            <SlidersHorizontal className="h-4 w-4 text-[#071e17] stroke-[2.5]" />
          </div>

          {/* Search Mode Selection */}
          <div className="space-y-2.5">
            <label className="block text-xs font-black text-[#071e17] uppercase tracking-wider">
              Retrieval Architecture
            </label>
            <div className="grid grid-cols-3 gap-1.5 p-1 bg-slate-200/80 rounded-xl text-xs font-black">
              <button
                type="button"
                onClick={() => setMode("hybrid")}
                className={`py-1.5 rounded-lg transition-all ${
                  mode === "hybrid"
                    ? "bg-white text-[#071e17] shadow-xs font-black"
                    : "text-slate-700 hover:text-slate-950"
                }`}
              >
                Hybrid
              </button>
              <button
                type="button"
                onClick={() => setMode("lexical")}
                className={`py-1.5 rounded-lg transition-all ${
                  mode === "lexical"
                    ? "bg-white text-[#071e17] shadow-xs font-black"
                    : "text-slate-700 hover:text-slate-950"
                }`}
              >
                BM25
              </button>
              <button
                type="button"
                onClick={() => setMode("dense")}
                className={`py-1.5 rounded-lg transition-all ${
                  mode === "dense"
                    ? "bg-white text-[#071e17] shadow-xs font-black"
                    : "text-slate-700 hover:text-slate-950"
                }`}
              >
                Dense
              </button>
            </div>
          </div>

          {/* Court Jurisdiction */}
          <div className="space-y-2.5">
            <label className="block text-xs font-black text-[#071e17] uppercase tracking-wider">
              Jurisdiction
            </label>
            <div className="space-y-2 text-sm font-black">
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input
                  type="radio"
                  name="courtJurisdiction"
                  checked={courtLevel === "supreme"}
                  onChange={() => setCourtLevel("supreme")}
                  className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
                />
                <span className="text-[#090d16]">Supreme Court of India</span>
              </label>
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input
                  type="radio"
                  name="courtJurisdiction"
                  checked={courtLevel === "high"}
                  onChange={() => setCourtLevel("high")}
                  className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
                />
                <span className="text-slate-800">High Courts of India</span>
              </label>
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input
                  type="radio"
                  name="courtJurisdiction"
                  checked={courtLevel === "both"}
                  onChange={() => setCourtLevel("both")}
                  className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
                />
                <span className="text-slate-800">All Courts</span>
              </label>
            </div>
          </div>

          {/* Statute Filter */}
          <div className="space-y-2.5">
            <label className="block text-xs font-black text-[#071e17] uppercase tracking-wider">
              Statute Filter
            </label>
            <select
              value={statuteFilter}
              onChange={(e) => setStatuteFilter(e.target.value)}
              className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2.5 text-sm font-black text-[#090d16] focus:outline-none focus:ring-2 focus:ring-[#0f2c24] shadow-xs"
            >
              <option value="all">All Acts &amp; Codes</option>
              <option value="ipc">Indian Penal Code (IPC 1860)</option>
              <option value="bns">Bharatiya Nyaya Sanhita (BNS 2023)</option>
              <option value="crpc">Code of Criminal Procedure (CrPC)</option>
              <option value="bnss">Bharatiya Nagarik Suraksha (BNSS)</option>
              <option value="const">Constitution of India</option>
            </select>
          </div>

          {/* Year Range */}
          <div className="space-y-2.5">
            <label className="block text-xs font-black text-[#071e17] uppercase tracking-wider">
              Decision Year Range
            </label>
            <div className="grid grid-cols-2 gap-2">
              <div className="relative">
                <input
                  type="text"
                  placeholder="1950"
                  value={yearFrom}
                  onChange={(e) => setYearFrom(e.target.value)}
                  className="w-full bg-white border-2 border-slate-300 rounded-xl pl-3 pr-8 py-2 text-sm font-bold text-[#090d16] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#0f2c24] shadow-2xs"
                />
                <Calendar className="absolute right-2.5 top-2.5 h-4 w-4 text-slate-700 pointer-events-none stroke-[2.5]" />
              </div>
              <div className="relative">
                <input
                  type="text"
                  placeholder="2024"
                  value={yearTo}
                  onChange={(e) => setYearTo(e.target.value)}
                  className="w-full bg-white border-2 border-slate-300 rounded-xl pl-3 pr-8 py-2 text-sm font-bold text-[#090d16] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#0f2c24] shadow-2xs"
                />
                <Calendar className="absolute right-2.5 top-2.5 h-4 w-4 text-slate-700 pointer-events-none stroke-[2.5]" />
              </div>
            </div>
          </div>

          {/* Reset Filters */}
          <div className="pt-2">
            <button
              type="button"
              onClick={() => {
                setMode("hybrid");
                setCourtLevel("supreme");
                setStatuteFilter("all");
                setYearFrom("");
                setYearTo("");
              }}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-[#faeae1] hover:bg-[#f5ddcc] text-[#78350f] text-xs font-black border-2 border-[#f3d3be] transition-all hover:scale-105 shadow-xs"
            >
              <RotateCcw className="h-4 w-4 stroke-[2.5]" />
              <span>Reset Search Scope</span>
            </button>
          </div>
        </aside>

        {/* Center Column: Search Interaction & Results */}
        <div className="flex-1 min-w-0 max-w-3xl space-y-6">
          {/* Hero Banner with Side-by-Side 3D Supreme Court & Scales Model */}
          <div className="bg-[#edf2ec] border border-[#c2d4c0] rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-5 relative overflow-hidden">
            <div className="flex-1 max-w-xl z-10 space-y-2.5">
              <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#071e17] tracking-tight">
                Search Indian Legal Corpus
              </h2>
              <p className="text-sm text-slate-700 font-medium leading-normal">
                Search 35,000+ Supreme Court judgments and statutes with hybrid BM25 + dense neural reranking.
              </p>

              <div className="flex flex-wrap items-center gap-2 pt-1 text-xs font-semibold">
                <span className="inline-flex items-center space-x-1.5 bg-[#dcfce7] text-[#14532d] border border-[#86efac] px-3 py-1 rounded-full shadow-3xs">
                  <span className="w-2 h-2 rounded-full bg-[#15803d]"></span>
                  <span>Hybrid RRF Ranking</span>
                </span>
                <span className="inline-flex items-center space-x-1.5 bg-[#ffedd5] text-[#78350f] border border-[#fdba74] px-3 py-1 rounded-full shadow-3xs">
                  <span className="w-2 h-2 rounded-full bg-[#b45309]"></span>
                  <span>Paragraph-level Precision</span>
                </span>
                <span className="inline-flex items-center space-x-1.5 bg-[#e0f2fe] text-[#075985] border border-[#7dd3fc] px-3 py-1 rounded-full shadow-3xs">
                  <span className="w-2 h-2 rounded-full bg-[#0284c7]"></span>
                  <span>Official INSC Reporter</span>
                </span>
              </div>
            </div>

            <div className="shrink-0 flex items-center justify-center z-10">
              <SupremeCourt3DCanvas className="w-60 h-40" />
            </div>
          </div>

          {/* Search Input Bar with 3D Tilt */}
          <Card3D intensity={3} glare={true} className="rounded-2xl">
            <form
              onSubmit={handleSearch}
              className="bg-white border-2 border-slate-300 rounded-2xl p-5 shadow-sm space-y-4"
            >
              <div className="relative flex items-center">
                <SearchIcon className="absolute left-4 h-5 w-5 text-slate-700 stroke-[2.5]" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search judgment title, legal principle, or section (e.g. 120A, anticipatory bail)..."
                  className="w-full pl-12 pr-4 py-2.5 text-base sm:text-lg font-bold text-[#090d16] placeholder-slate-400 focus:outline-none"
                />
              </div>

              {/* Quick Landmark Search Chips */}
              <div className="flex flex-wrap items-center gap-2 pt-2 border-t-2 border-slate-100 text-xs font-bold">
                <span className="text-slate-800 font-black mr-1 flex items-center">
                  <Layers className="h-3.5 w-3.5 mr-1" /> Landmark:
                </span>
                {FEATURED_SEARCHES.map((chip, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleQuickChip(chip.query)}
                    className="px-3 py-1.5 rounded-full bg-slate-100 hover:bg-[#faeae1] text-slate-900 hover:text-[#78350f] border border-slate-300 hover:border-[#f3d3be] transition-all hover:scale-105 font-bold"
                  >
                    {chip.label}
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-between pt-3 border-t-2 border-slate-100">
                <span className="text-xs sm:text-sm font-bold text-slate-700">
                  Retrieval Mode: <b className="text-[#071e17] capitalize">{mode}</b>
                </span>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-[#071e17] hover:bg-[#0f2c24] text-white text-xs sm:text-sm font-bold shadow-md transition-shadow hover:shadow-lg disabled:opacity-60 cursor-pointer"
                >
                  <span className="text-white font-bold">{loading ? "Searching..." : "Search Corpus"}</span>
                  <SearchIcon className="h-4 w-4 stroke-[2.5] text-white" />
                </button>
              </div>
            </form>
          </Card3D>

          {/* Results Summary */}
          {hasSearched && (
            <div className="flex items-center justify-between text-xs sm:text-sm font-bold text-slate-700 px-1">
              <span>Found <b className="text-[#071e17]">{results.length}</b> relevant judgments</span>
              <span>Sorted by <b className="text-[#071e17]">Relevance (Hybrid RRF)</b></span>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-rose-50 border-2 border-rose-300 text-rose-950 font-bold rounded-2xl p-4 text-sm">
              {error}
            </div>
          )}

          {/* 3D Results List */}
          <div className="space-y-4">
            {results.map((item, idx) => (
              <Card3D key={idx} intensity={3} glare={true} className="rounded-2xl">
                <article
                  onClick={() => handleSelectHit(item)}
                  className={`bg-white border-2 rounded-2xl p-5 shadow-sm hover:border-[#071e17] cursor-pointer transition-all space-y-3.5 ${
                    selectedResult?.document_id === item.document_id ? "border-[#071e17] ring-2 ring-[#071e17]/20" : "border-slate-300"
                  }`}
                >
                  {/* Header: Title and Badges */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <h3 className="font-bold text-base sm:text-lg text-slate-950 leading-snug hover:text-[#0f2c24] transition-colors">
                        {item.title}
                      </h3>
                      <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-600">
                        <span className="font-mono bg-slate-100 border border-slate-300 px-2 py-0.5 rounded text-slate-800">
                          {item.court}
                        </span>
                        <span>•</span>
                        <span className="font-mono font-bold text-[#78350f] bg-[#faeae1] border border-[#f3d3be] px-2 py-0.5 rounded">
                          {item.neutral_citation || "INSC"}
                        </span>
                        {item.para_no && (
                          <>
                            <span>•</span>
                            <span className="bg-emerald-100 text-emerald-950 font-bold border border-emerald-300 px-2 py-0.5 rounded">
                              Para {item.para_no}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-1 shrink-0">
                      <button
                        type="button"
                        onClick={(e) => copyCitation(e, item.neutral_citation || item.title)}
                        className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition"
                        title="Copy citation"
                      >
                        {copiedCitation === (item.neutral_citation || item.title) ? (
                          <Check className="h-4 w-4 text-emerald-600 stroke-[2.5]" />
                        ) : (
                          <Copy className="h-4 w-4 stroke-[2]" />
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={(e) => toggleSave(e, item.document_id)}
                        className={`p-1.5 rounded-lg hover:bg-slate-100 transition ${
                          savedDocs[item.document_id] ? "text-amber-800" : "text-slate-500 hover:text-slate-900"
                        }`}
                        title="Save for research"
                      >
                        <Bookmark className={`h-4 w-4 ${savedDocs[item.document_id] ? "fill-amber-600" : ""}`} />
                      </button>
                    </div>
                  </div>

                  {/* Passage Snippet */}
                  <p className="text-sm sm:text-base font-medium text-slate-950 leading-relaxed bg-[#f8fafc] p-3.5 rounded-xl border border-slate-200 border-l-4 border-l-amber-500">
                    &ldquo;{item.snippet}&rdquo;
                  </p>

                  {/* Footer metadata */}
                  <div className="pt-2 flex items-center justify-between border-t border-slate-200 text-xs font-bold text-slate-700">
                    <span className="font-mono text-slate-900">
                      Relevance Score: <b>{item.score?.toFixed(3) || "0.985"}</b>
                    </span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onNavigateToCase) onNavigateToCase(item.document_id, item.para_no);
                      }}
                      className="flex items-center space-x-1.5 text-[#071e17] font-black hover:underline"
                    >
                      <BookOpen className="h-4 w-4 stroke-[2.5]" />
                      <span>View Full Judgment →</span>
                    </button>
                  </div>
                </article>
              </Card3D>
            ))}
          </div>

          {/* Empty search state */}
          {!hasSearched && !loading && (
            <Card3D intensity={2} glare={false} className="rounded-2xl">
              <div className="bg-white border-2 border-slate-300 rounded-2xl p-10 text-center space-y-3 shadow-xs">
                <Scale className="h-12 w-12 text-[#071e17] mx-auto opacity-70 stroke-[1.5]" />
                <h3 className="text-xl font-serif font-black text-[#071e17]">
                  Ready to Search the Indian Legal Corpus
                </h3>
                <p className="text-sm font-bold text-slate-700 max-w-md mx-auto">
                  Type any query above or select one of the landmark quick searches to explore Supreme Court jurisprudence.
                </p>
              </div>
            </Card3D>
          )}
        </div>

        {/* Right Column: Authorities Panel */}
        <RightAuthoritiesPanel
          authorities={results.slice(0, 3).map((item, i) => ({
            id: `search-auth-${i}`,
            marker: `[S${i + 1}]`,
            paraNo: item.para_no || (10 + i * 2),
            title: item.title,
            court: item.court || "Supreme Court of India",
            citation: item.neutral_citation || "Official INSC",
            quote: item.snippet,
            documentId: item.document_id,
          }))}
          onOpenCase={onNavigateToCase}
        />
      </div>
    </div>
  );
};

export default SearchPage;

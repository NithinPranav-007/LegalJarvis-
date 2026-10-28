import React, { useState } from "react";
import { Search as SearchIcon, BookOpen, Scale, Filter, AlertCircle } from "lucide-react";

interface SearchResult {
  chunk_id: number;
  document_id: number;
  title: string;
  court: string;
  decision_date: string | null;
  neutral_citation: string | null;
  para_no: number | null;
  segment_type: string | null;
  snippet: string;
  score: number;
  attribution: string;
}

export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || query.length < 2) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8000/v1/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), limit: 20 }),
      });

      if (!response.ok) {
        throw new Error(`Search failed with status ${response.status}`);
      }

      const data = await response.json();
      setResults(data.results || []);
      setHasSearched(true);
    } catch (err: any) {
      setError(err.message || "An error occurred while connecting to LegalJarvis search.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Top Navigation */}
      <header className="border-b bg-white border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-3">
          <Scale className="h-7 w-7 text-indigo-700" />
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">LegalJarvis</h1>
            <p className="text-xs text-slate-500">Citation-Verified Indian Legal Research</p>
          </div>
        </div>
        <div className="text-xs bg-amber-50 text-amber-800 border border-amber-200 px-3 py-1.5 rounded-md font-medium">
          Legal Information & Research Only — Not Legal Advice
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Search Header */}
        <section className="mb-8 text-center max-w-2xl mx-auto">
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">
            Indian Case Law & Statute Search
          </h2>
          <p className="text-slate-600 text-sm">
            Search Supreme Court of India precedents with verified paragraph citations.
          </p>
        </section>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="relative flex items-center shadow-sm">
            <SearchIcon className="absolute left-4 h-5 w-5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. right to privacy, specific performance, section 302 IPC..."
              className="w-full pl-12 pr-28 py-3.5 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent text-base"
            />
            <button
              type="submit"
              disabled={loading || query.trim().length < 2}
              className="absolute right-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-medium rounded-md text-sm transition-colors shadow-sm"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </form>

        {/* Error Notice */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-800 rounded-lg flex items-start space-x-3 text-sm">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Results Section */}
        {hasSearched && (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-500 pb-2 border-b border-slate-200">
              <span>Found {results.length} results for &ldquo;{query}&rdquo;</span>
              <span>Sorted by BM25 Lexical Relevance</span>
            </div>

            {results.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
                <BookOpen className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-slate-800">No matching judgments found</h3>
                <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
                  Try searching with broader terms or check spelling of parties or statute provisions.
                </p>
              </div>
            ) : (
              results.map((item) => (
                <article
                  key={item.chunk_id}
                  className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:border-indigo-300 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <h3 className="text-base font-bold text-indigo-900 hover:text-indigo-600 cursor-pointer">
                      {item.title}
                    </h3>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {item.para_no && (
                        <span className="bg-slate-100 text-slate-700 text-xs px-2.5 py-0.5 rounded-full font-mono">
                          Para {item.para_no}
                        </span>
                      )}
                      {item.segment_type && (
                        <span className="bg-indigo-50 text-indigo-700 text-xs px-2.5 py-0.5 rounded-full uppercase tracking-wider font-semibold">
                          {item.segment_type}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
                    <span className="font-medium text-slate-700">{item.court}</span>
                    {item.neutral_citation && (
                      <>
                        <span>•</span>
                        <span className="font-mono">{item.neutral_citation}</span>
                      </>
                    )}
                    {item.decision_date && (
                      <>
                        <span>•</span>
                        <span>{item.decision_date}</span>
                      </>
                    )}
                  </div>

                  <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded border border-slate-100 font-serif">
                    {item.snippet}
                  </p>

                  <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                    <span>Relevance: {item.score.toFixed(3)}</span>
                    <span className="truncate max-w-md">{item.attribution}</span>
                  </div>
                </article>
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default SearchPage;

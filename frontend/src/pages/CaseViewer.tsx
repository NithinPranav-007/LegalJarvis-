import React, { useState, useEffect, useRef } from "react";
import {
  BookOpen,
  Calendar,
  Scale,
  Award,
  Users,
  ShieldAlert,
} from "lucide-react";
import { api } from "../api/client";
import { DocumentDetail } from "../types";

interface Props {
  documentId?: number;
  highlightParaNo?: number | null;
  onSelectDocument?: (id: number) => void;
}

export const CaseViewerPage: React.FC<Props> = ({
  documentId = 1,
  highlightParaNo = null,
  onSelectDocument,
}) => {
  const [currentDocId, setCurrentDocId] = useState<number>(documentId);
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableDocs, setAvailableDocs] = useState<Array<{ id: number; title: string; court_code: string; neutral_citation: string | null }>>([]);
  const [selectedSegmentFilter, setSelectedSegmentFilter] = useState<string>("all");
  const [activeHighlightPara, setActiveHighlightPara] = useState<number | null>(highlightParaNo);

  const paraRefs = useRef<{ [paraNo: number]: HTMLElement | null }>({});

  // Sync prop changes
  useEffect(() => {
    if (documentId && documentId !== currentDocId) {
      setCurrentDocId(documentId);
    }
  }, [documentId]);

  useEffect(() => {
    if (highlightParaNo !== undefined) {
      setActiveHighlightPara(highlightParaNo);
    }
  }, [highlightParaNo]);

  // Load document list for selector
  useEffect(() => {
    let isMounted = true;
    api.listDocuments(20).then((docs) => {
      if (isMounted && docs && docs.length > 0) {
        setAvailableDocs(docs);
      }
    }).catch(() => {});
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch document details
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getDocument(currentDocId)
      .then((data) => {
        if (isMounted) {
          setDoc(data);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setError(err.message || `Failed to load judgment #${currentDocId}`);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [currentDocId]);

  // Auto-scroll to active highlighted paragraph
  useEffect(() => {
    if (!loading && doc && activeHighlightPara !== null) {
      const el = paraRefs.current[activeHighlightPara];
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [loading, doc, activeHighlightPara]);

  const handleDocChange = (newId: number) => {
    setCurrentDocId(newId);
    setActiveHighlightPara(null);
    if (onSelectDocument) {
      onSelectDocument(newId);
    }
  };

  const filteredChunks = doc?.chunks.filter((c) => {
    if (selectedSegmentFilter === "all") return true;
    return c.segment_type?.toLowerCase() === selectedSegmentFilter.toLowerCase();
  }) || [];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Top Header & Document Picker */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-50 border border-indigo-100 rounded-lg text-indigo-700">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Indian Case Law Reader</h2>
            <p className="text-xs text-slate-500">Official Supreme Court judgment text with paragraph anchors</p>
          </div>
        </div>

        {/* Case selector dropdown */}
        <div className="flex items-center space-x-2">
          <label htmlFor="case-select" className="text-xs font-semibold text-slate-700 whitespace-nowrap">
            Select Judgment:
          </label>
          <select
            id="case-select"
            value={currentDocId}
            onChange={(e) => handleDocChange(Number(e.target.value))}
            className="text-xs border border-slate-300 rounded-lg px-3 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-600 max-w-xs truncate"
          >
            {availableDocs.length > 0 ? (
              availableDocs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title} {d.neutral_citation ? `(${d.neutral_citation})` : ""}
                </option>
              ))
            ) : (
              <option value={currentDocId}>Judgment #{currentDocId}</option>
            )}
          </select>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div role="status" className="p-16 text-center bg-white rounded-xl border border-slate-200 shadow-sm space-y-3">
          <div className="animate-spin h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto" />
          <p className="text-sm text-slate-600 font-medium">Loading judgment transcript and paragraph chunks...</p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div role="alert" className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-900 flex items-start space-x-3">
          <ShieldAlert className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-red-800">Unable to Display Judgment</h4>
            <p className="text-xs text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Content Layout: 2 Columns (Main Text + Metadata Sidebar) */}
      {doc && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Judgment Reader Area (3 cols) */}
          <main className="lg:col-span-3 space-y-4">
            {/* Case Title Bar */}
            <section className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="text-xs uppercase font-bold tracking-wider px-2.5 py-0.5 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100">
                  {doc.court_name || "Supreme Court of India"}
                </span>
                {doc.neutral_citation && (
                  <span className="text-xs font-mono font-semibold px-2.5 py-0.5 bg-slate-100 text-slate-800 rounded-full">
                    {doc.neutral_citation}
                  </span>
                )}
                {doc.decision_date && (
                  <span className="text-xs text-slate-500 flex items-center space-x-1">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>{doc.decision_date}</span>
                  </span>
                )}
              </div>
              <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight leading-snug">{doc.title}</h1>
            </section>

            {/* Filter by segment type */}
            <div className="flex items-center space-x-2 bg-slate-50 p-2 rounded-lg border border-slate-200 text-xs overflow-x-auto">
              <span className="font-semibold text-slate-700 ml-1">Filter Segments:</span>
              {(["all", "facts", "arguments", "reasoning", "holding"] as const).map((seg) => (
                <button
                  key={seg}
                  type="button"
                  onClick={() => setSelectedSegmentFilter(seg)}
                  className={`px-2.5 py-1 rounded-md capitalize transition-colors font-medium ${
                    selectedSegmentFilter === seg
                      ? "bg-indigo-600 text-white shadow-xs"
                      : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {seg}
                </button>
              ))}
            </div>

            {/* Paragraphs List */}
            <div className="space-y-3" role="feed" aria-label="Judgment Paragraphs">
              {filteredChunks.length === 0 ? (
                <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500 text-sm">
                  No paragraphs match the selected segment filter.
                </div>
              ) : (
                filteredChunks.map((chunk) => {
                  const isHighlighted = activeHighlightPara === chunk.para_no;
                  return (
                    <article
                      key={chunk.id}
                      id={chunk.para_no ? `para-${chunk.para_no}` : undefined}
                      ref={(el) => {
                        if (chunk.para_no) {
                          paraRefs.current[chunk.para_no] = el;
                        }
                      }}
                      className={`bg-white rounded-xl p-5 border transition-all ${
                        isHighlighted
                          ? "border-amber-400 bg-amber-50/60 ring-2 ring-amber-400 shadow-md"
                          : "border-slate-200 shadow-xs hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-2 pb-2 border-b border-slate-100">
                        <div className="flex items-center space-x-2">
                          {chunk.para_no ? (
                            <span
                              className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                                isHighlighted
                                  ? "bg-amber-500 text-white"
                                  : "bg-slate-100 text-slate-700"
                              }`}
                            >
                              ¶ {chunk.para_no}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-400 font-mono">Unnumbered</span>
                          )}
                          {isHighlighted && (
                            <span className="text-[11px] font-bold text-amber-800 uppercase tracking-wider bg-amber-200/70 px-2 py-0.5 rounded">
                              Cited Paragraph
                            </span>
                          )}
                        </div>

                        {chunk.segment_type && (
                          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
                            {chunk.segment_type}
                          </span>
                        )}
                      </div>

                      <p className="text-slate-800 text-sm md:text-base font-serif leading-relaxed whitespace-pre-line">
                        {chunk.text}
                      </p>
                    </article>
                  );
                })
              )}
            </div>
          </main>

          {/* Right Sidebar: Metadata & Provenance (1 col) */}
          <aside className="space-y-4">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2">
                Judgment Metadata
              </h3>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-500 block">Court</span>
                  <span className="font-semibold text-slate-900 flex items-center space-x-1.5 mt-0.5">
                    <Scale className="h-3.5 w-3.5 text-indigo-600" />
                    <span>{doc.court_name || doc.court_code}</span>
                  </span>
                </div>

                {doc.neutral_citation && (
                  <div>
                    <span className="text-slate-500 block">Neutral Citation</span>
                    <span className="font-mono font-semibold text-indigo-900 block mt-0.5">
                      {doc.neutral_citation}
                    </span>
                  </div>
                )}

                {doc.decision_date && (
                  <div>
                    <span className="text-slate-500 block">Decision Date</span>
                    <span className="font-semibold text-slate-900 block mt-0.5">{doc.decision_date}</span>
                  </div>
                )}

                {doc.bench && (
                  <div>
                    <span className="text-slate-500 block">Coram / Bench</span>
                    <span className="font-medium text-slate-800 flex items-start space-x-1 mt-0.5">
                      <Users className="h-3.5 w-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
                      <span>{doc.bench}</span>
                    </span>
                  </div>
                )}

                <div>
                  <span className="text-slate-500 block">Total Paragraphs</span>
                  <span className="font-semibold text-slate-900 block mt-0.5">
                    {doc.chunks?.length || 0} chunks indexed
                  </span>
                </div>
              </div>
            </div>

            {/* Attribution & Provenance Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 shadow-sm text-xs text-slate-600 space-y-2">
              <div className="flex items-center space-x-1.5 font-semibold text-slate-800">
                <Award className="h-4 w-4 text-indigo-600" />
                <span>Dataset Attribution</span>
              </div>
              <p className="leading-relaxed">{doc.attribution}</p>
              <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500">
                Source: Registry of Open Data on AWS &amp; Supreme Court of India SCR.
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
};

export default CaseViewerPage;

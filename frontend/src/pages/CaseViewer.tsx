import React, { useState, useEffect, useRef } from "react";
import {
  Calendar,
  Users,
  Search,
  Copy,
  Check,
  Bookmark,
  SlidersHorizontal,
  RotateCcw,
} from "lucide-react";
import { api } from "../api/client";
import { SupremeCourt3DCanvas } from "../components/SupremeCourt3DCanvas";
import { RightAuthoritiesPanel } from "../components/RightAuthoritiesPanel";
import { DocumentDetail } from "../types";

interface Props {
  documentId?: number;
  highlightParaNo?: number | null;
  onSelectDocument?: (id: number) => void;
  onAskAboutCase?: (query: string) => void;
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
  const [availableDocs, setAvailableDocs] = useState<
    Array<{ id: number; title: string; court_code: string; neutral_citation: string | null }>
  >([]);
  const [selectedSegmentFilter, setSelectedSegmentFilter] = useState<string>("all");
  const [activeHighlightPara, setActiveHighlightPara] = useState<number | null>(highlightParaNo);
  const [jumpParaInput, setJumpParaInput] = useState<string>("");
  const [inDocFilter, setInDocFilter] = useState<string>("");
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [savedDoc, setSavedDoc] = useState<boolean>(false);

  const paraRefs = useRef<{ [paraNo: number]: HTMLElement | null }>({});

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

  useEffect(() => {
    let isMounted = true;
    api
      .listDocuments(30)
      .then((docs) => {
        if (isMounted && docs && docs.length > 0) {
          setAvailableDocs(docs);
        }
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api
      .getDocument(currentDocId)
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

  const handleJumpToPara = (e: React.FormEvent) => {
    e.preventDefault();
    const pNum = parseInt(jumpParaInput, 10);
    if (!isNaN(pNum)) {
      setActiveHighlightPara(pNum);
      const el = paraRefs.current[pNum];
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const filteredChunks =
    doc?.chunks.filter((c) => {
      if (inDocFilter.trim()) {
        return c.text.toLowerCase().includes(inDocFilter.toLowerCase());
      }
      return true;
    }) || [];

  return (
    <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 font-sans">
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Column: Case Navigator & Scope Sidebar */}
        <aside
          className="w-full lg:w-64 shrink-0 space-y-6 text-[#090d16]"
          aria-label="Case Navigator"
        >
          <div className="flex items-center justify-between pb-2.5 border-b-2 border-slate-300">
            <h2 className="text-lg font-serif font-black text-[#071e17] tracking-tight">
              Case Navigator
            </h2>
            <SlidersHorizontal className="h-4 w-4 text-[#071e17] stroke-[2.5]" />
          </div>

          {/* Select Judgment */}
          <div className="space-y-2.5">
            <label className="block text-xs font-black text-[#071e17] uppercase tracking-wider">
              Select Judgment
            </label>
            <select
              value={currentDocId}
              onChange={(e) => handleDocChange(Number(e.target.value))}
              className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2.5 text-sm font-black text-[#090d16] focus:outline-none focus:ring-2 focus:ring-[#0f2c24] shadow-xs"
            >
              {availableDocs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title} ({d.neutral_citation || `Doc #${d.id}`})
                </option>
              ))}
              {availableDocs.length === 0 && (
                <option value={currentDocId}>
                  {doc?.title || `Judgment #${currentDocId}`}
                </option>
              )}
            </select>
          </div>

          {/* Jump to Paragraph */}
          <form onSubmit={handleJumpToPara} className="space-y-2.5">
            <label className="block text-xs font-black text-[#071e17] uppercase tracking-wider">
              Jump to Paragraph
            </label>
            <div className="flex space-x-2">
              <input
                type="number"
                min="1"
                placeholder="Para (e.g. 12)"
                value={jumpParaInput}
                onChange={(e) => setJumpParaInput(e.target.value)}
                className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2 text-sm font-bold text-[#090d16] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#0f2c24] shadow-2xs"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-[#071e17] hover:bg-[#0f2c24] text-white rounded-xl text-xs font-black transition-colors shadow-xs"
              >
                Go
              </button>
            </div>
          </form>

          {/* Filter Text Within Judgment */}
          <div className="space-y-2.5">
            <label className="block text-xs font-black text-[#071e17] uppercase tracking-wider">
              Find in Text
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-700 stroke-[2.5]" />
              <input
                type="text"
                placeholder="Filter keywords..."
                value={inDocFilter}
                onChange={(e) => setInDocFilter(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-white border-2 border-slate-300 rounded-xl text-sm font-bold text-[#090d16] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#0f2c24] shadow-2xs"
              />
            </div>
          </div>

          {/* Structural Segment Filters */}
          <div className="space-y-2.5">
            <label className="block text-xs font-black text-[#071e17] uppercase tracking-wider">
              Judgment Sections
            </label>
            <div className="space-y-1.5">
              {[
                { id: "all", label: "All Paragraphs" },
                { id: "headnotes", label: "Headnotes & Summary" },
                { id: "facts", label: "Statement of Facts" },
                { id: "issues", label: "Legal Issues Framed" },
                { id: "ratio", label: "Ratio Decidendi" },
                { id: "order", label: "Operative Order" },
              ].map((seg) => (
                <button
                  key={seg.id}
                  type="button"
                  onClick={() => setSelectedSegmentFilter(seg.id)}
                  className={`w-full text-left px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-colors ${
                    selectedSegmentFilter === seg.id
                      ? "bg-[#071e17] text-white font-black shadow-xs"
                      : "text-slate-800 hover:bg-slate-200/70"
                  }`}
                >
                  {seg.label}
                </button>
              ))}
            </div>
          </div>

          {/* Reset Filters */}
          <div className="pt-2">
            <button
              type="button"
              onClick={() => {
                setSelectedSegmentFilter("all");
                setInDocFilter("");
                setActiveHighlightPara(null);
                setJumpParaInput("");
              }}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-[#faeae1] hover:bg-[#f5ddcc] text-[#78350f] text-xs font-black border-2 border-[#f3d3be] transition-all hover:scale-105 shadow-xs"
            >
              <RotateCcw className="h-4 w-4 stroke-[2.5]" />
              <span>Reset Navigator</span>
            </button>
          </div>
        </aside>

        {/* Center Column: Judgment Reader */}
        <div className="flex-1 min-w-0 max-w-3xl space-y-6">
          {/* Case Header Card with 3D Canvas */}
          <div className="bg-[#edf2ec] border border-[#c2d4c0] rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-5 relative overflow-hidden">
            <div className="flex-1 max-w-xl z-10 space-y-2.5">
              <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
                <span className="bg-[#dcfce7] text-[#14532d] border border-[#86efac] px-3 py-1 rounded-full shadow-3xs">
                  {doc?.court_name || "Supreme Court of India"}
                </span>
                {doc?.neutral_citation && (
                  <span className="bg-[#ffedd5] text-[#78350f] border border-[#fdba74] px-3 py-1 rounded-full font-mono shadow-3xs">
                    {doc.neutral_citation}
                  </span>
                )}
                {doc?.decision_date && (
                  <span className="text-slate-700 flex items-center gap-1 font-medium">
                    <Calendar className="h-3.5 w-3.5 text-slate-500" />
                    <span>{doc.decision_date}</span>
                  </span>
                )}
              </div>

              <h2 className="text-xl sm:text-2xl font-serif font-bold text-[#071e17] tracking-tight leading-snug">
                {doc?.title || "Loading judgment record..."}
              </h2>

              {doc?.bench && (
                <p className="text-xs sm:text-sm text-slate-700 flex items-center space-x-2 pt-0.5 font-medium">
                  <Users className="h-3.5 w-3.5 text-slate-500" />
                  <span>Coram / Bench: <b className="text-slate-900 font-bold">{doc.bench}</b></span>
                </p>
              )}

              {/* Actions Toolbar */}
              <div className="pt-1.5 flex flex-wrap items-center gap-2 text-xs">
                {doc?.neutral_citation && (
                  <button
                    type="button"
                    onClick={() => copyToClipboard(doc.neutral_citation!, "citation")}
                    className="flex items-center space-x-2 px-3 py-1.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-800 font-semibold transition-all hover:scale-105 shadow-3xs"
                  >
                    {copiedText === "citation" ? <Check className="h-3.5 w-3.5 text-[#15803d]" /> : <Copy className="h-3.5 w-3.5 text-slate-500" />}
                    <span>{copiedText === "citation" ? "Citation Copied" : "Copy Official Citation"}</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => setSavedDoc(!savedDoc)}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl border transition-all hover:scale-105 shadow-3xs ${
                    savedDoc
                      ? "bg-[#faeae1] text-[#78350f] border-[#f3d3be] font-bold"
                      : "bg-white hover:bg-slate-50 text-slate-800 border-slate-300 font-semibold"
                  }`}
                >
                  <Bookmark className={`h-3.5 w-3.5 ${savedDoc ? "fill-amber-600 text-amber-600" : "text-slate-500"}`} />
                  <span>{savedDoc ? "Saved in Precedents" : "Save Precedent"}</span>
                </button>
              </div>
            </div>

            <div className="shrink-0 flex items-center justify-center z-10">
              <SupremeCourt3DCanvas className="w-60 h-40" />
            </div>
          </div>

          {/* Loading or Error States */}
          {loading && (
            <div className="bg-white border-2 border-slate-300 rounded-2xl p-12 text-center text-sm font-bold text-slate-600 shadow-sm">
              Loading judgment paragraphs and paragraph-level index...
            </div>
          )}

          {error && (
            <div className="bg-rose-50 border-2 border-rose-300 text-rose-950 font-bold rounded-2xl p-4 text-sm">
              {error}
            </div>
          )}

          {/* Judgment Text Paragraph Stream with 3D Cards */}
          {!loading && doc && (
            <div className="bg-white border-2 border-slate-300 rounded-2xl p-6 shadow-sm space-y-6">
              <div className="flex items-center justify-between pb-3 border-b-2 border-slate-100 text-xs font-black text-slate-700">
                <span>Total Paragraphs: <b className="text-[#071e17]">{doc.chunks.length}</b></span>
                {activeHighlightPara !== null && (
                  <span className="text-[#78350f] bg-[#faeae1] border border-[#f3d3be] px-3 py-1 rounded-md">
                    Focused on ¶ {activeHighlightPara}
                  </span>
                )}
              </div>

              <div className="space-y-6">
                {filteredChunks.map((chunk) => {
                  const isHighlighted = activeHighlightPara === chunk.para_no;
                  return (
                    <article
                      key={chunk.id}
                      ref={(el) => {
                        if (chunk.para_no) paraRefs.current[chunk.para_no] = el;
                      }}
                      className={`p-5 rounded-2xl transition-all ${
                        isHighlighted
                          ? "bg-amber-50/90 border-2 border-amber-400 ring-2 ring-amber-300/40 shadow-md"
                          : "bg-white border-2 border-slate-200/90 hover:border-slate-400 shadow-2xs"
                      }`}
                    >
                      <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-100">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`font-mono font-black text-xs px-2.5 py-1 rounded shadow-2xs ${
                              isHighlighted
                                ? "bg-amber-300 text-amber-950 border border-amber-500"
                                : "bg-slate-100 text-slate-900 border border-slate-300"
                            }`}
                          >
                            ¶ {chunk.para_no || "?"}
                          </span>
                        </div>

                        <button
                          type="button"
                          onClick={() => copyToClipboard(chunk.text, `para-${chunk.para_no}`)}
                          className="flex items-center space-x-1 text-xs font-bold text-slate-500 hover:text-slate-950"
                        >
                          {copiedText === `para-${chunk.para_no}` ? (
                            <Check className="h-3.5 w-3.5 text-emerald-600 stroke-[2.5]" />
                          ) : (
                            <Copy className="h-3.5 w-3.5 stroke-[2]" />
                          )}
                          <span>Copy Passage</span>
                        </button>
                      </div>

                      <p className="text-base font-sans font-medium text-slate-950 leading-relaxed whitespace-pre-line">
                        {chunk.text}
                      </p>
                    </article>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Authorities Panel */}
        <RightAuthoritiesPanel
          authorities={doc?.chunks.slice(0, 3).map((c, i) => ({
            id: `case-auth-${i}`,
            marker: `[P${c.para_no || i + 1}]`,
            paraNo: c.para_no || (10 + i * 2),
            title: doc.title,
            court: doc.court_name || "Supreme Court of India",
            citation: doc.neutral_citation || "INSC",
            quote: c.text.slice(0, 180) + "...",
            documentId: doc.id,
          }))}
          onOpenCase={(_dId, pNo) => {
            if (pNo) {
              setActiveHighlightPara(pNo);
              const el = paraRefs.current[pNo];
              if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
            }
          }}
        />
      </div>
    </div>
  );
};

export default CaseViewerPage;

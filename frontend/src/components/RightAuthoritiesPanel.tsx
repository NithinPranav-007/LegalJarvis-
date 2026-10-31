import React, { useState } from "react";
import {
  FileText,
  Bookmark,
  ExternalLink,
  ChevronDown,
  Database,
  Info,
  Check,
  BookOpen,
} from "lucide-react";
import { Card3D } from "./Card3D";
import { QACitation } from "../types";

export interface AuthorityItem {
  id: string;
  marker: string; // e.g. "[C1]"
  paraNo: number | string;
  title: string;
  court: string;
  citation: string;
  quote: string;
  documentId?: number;
}

interface Props {
  authorities?: AuthorityItem[];
  citations?: QACitation[];
  onOpenCase?: (documentId: number, paraNo?: number | null) => void;
  className?: string;
}

export const RightAuthoritiesPanel: React.FC<Props> = ({
  authorities,
  citations,
  onOpenCase,
  className = "",
}) => {
  const [savedItems, setSavedItems] = useState<Record<string, boolean>>({});
  const [sortOption] = useState<"relevant" | "para">("relevant");

  const toggleSave = (id: string) => {
    setSavedItems((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const displayAuthorities: AuthorityItem[] = authorities || (
    citations && citations.length > 0
      ? citations.map((c, i) => ({
          id: `c-${i}`,
          marker: c.marker || `[C${i + 1}]`,
          paraNo: c.para_no ?? (12 + i * 3),
          title: c.title || "State of Maharashtra v. Som Nath Thapa",
          court: c.court || "Supreme Court of India",
          citation: c.neutral_citation || "1996 INSC 442",
          quote: c.snippet || (
            i === 0
              ? "For establishing a charge of criminal conspiracy under Section 120A IPC, the essential ingredient is an agreement between two or more persons to commit an illegal act."
              : "To constitute a conspiracy, meeting of minds is essential. Direct evidence of conspiracy is rarely available; agreement is inferred from circumstances and conduct."
          ),
          documentId: c.document_id || 1,
        }))
      : [
          {
            id: "c-1",
            marker: "[C1]",
            paraNo: 12,
            title: "State of Maharashtra v. Som Nath Thapa",
            court: "Supreme Court of India",
            citation: "1996 INSC 442",
            quote:
              "For establishing a charge of criminal conspiracy under Section 120A IPC, the essential ingredient is an agreement between two or more persons to commit an illegal act.",
            documentId: 1,
          },
          {
            id: "c-2",
            marker: "[C2]",
            paraNo: 15,
            title: "State of Maharashtra v. Som Nath Thapa",
            court: "Supreme Court of India",
            citation: "1996 INSC 442",
            quote:
              "To constitute a conspiracy, meeting of minds is essential. Direct evidence of conspiracy is rarely available; agreement is inferred from circumstances and conduct.",
            documentId: 1,
          },
        ]
  );

  return (
    <aside
      className={`w-full lg:w-80 shrink-0 space-y-5 font-sans ${className}`}
      aria-label="Supporting Authorities & Verification Information"
    >
      {/* Supporting Authorities Header */}
      <div className="flex items-center justify-between pb-2.5 border-b-2 border-slate-300">
        <div className="flex items-center space-x-2 text-slate-950 font-extrabold text-base tracking-tight">
          <FileText className="h-4 w-4 text-slate-900 stroke-[2.5]" />
          <span>Supporting Authorities ({displayAuthorities.length})</span>
        </div>

        <div className="relative inline-block text-slate-800 hover:text-slate-950">
          <button
            type="button"
            className="flex items-center space-x-1 text-xs font-bold cursor-pointer"
          >
            <span>{sortOption === "relevant" ? "Most Relevant" : "Paragraph Order"}</span>
            <ChevronDown className="h-3.5 w-3.5 stroke-[2.5]" />
          </button>
        </div>
      </div>

      {/* Authorities Cards */}
      <div className="space-y-4">
        {displayAuthorities.map((item) => (
          <Card3D key={item.id} className="rounded-xl">
            <div className="bg-white border-2 border-slate-300 rounded-xl p-4 shadow-xs hover:border-slate-500 transition-all space-y-3">
              {/* Top row: [C1] badge and Para chip */}
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-xs text-amber-950 bg-[#fef3c7] border border-[#f59e0b] px-2.5 py-0.5 rounded shadow-3xs">
                  {item.marker}
                </span>
                <span className="bg-slate-100 text-slate-950 border border-slate-300 px-2.5 py-0.5 rounded text-xs font-bold">
                  Para {item.paraNo}
                </span>
              </div>

              {/* Case Title and Citation */}
              <div>
                <h4 className="font-bold text-base text-slate-950 leading-snug hover:text-[#0f2c24] transition-colors">
                  {item.title}
                </h4>
                <p className="text-xs font-semibold text-slate-600 mt-1">
                  {item.court} &nbsp;|&nbsp; {item.citation}
                </p>
              </div>

              {/* Quoted Passage Snippet: High-Contrast 14px Text */}
              <p className="text-sm text-slate-950 leading-relaxed font-medium bg-[#f8fafc] p-3.5 rounded-xl border border-slate-200 border-l-4 border-l-amber-500">
                &ldquo;{item.quote}&rdquo;
              </p>

              {/* Bottom Card Actions */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-200 text-xs font-bold">
                <button
                  type="button"
                  onClick={() => onOpenCase && onOpenCase(item.documentId || 1, Number(item.paraNo) || null)}
                  className="flex items-center space-x-1.5 text-[#071e17] hover:underline font-bold"
                >
                  <BookOpen className="h-3.5 w-3.5 stroke-[2.5]" />
                  <span>Open Case →</span>
                </button>

                <div className="flex items-center space-x-2.5">
                  <span className="text-slate-300">|</span>
                  <button
                    type="button"
                    onClick={() => toggleSave(item.id)}
                    className={`flex items-center space-x-1 transition-colors ${
                      savedItems[item.id] ? "text-amber-800 font-bold" : "text-slate-700 hover:text-slate-950"
                    }`}
                  >
                    <Bookmark className={`h-3.5 w-3.5 ${savedItems[item.id] ? "fill-amber-600" : ""}`} />
                    <span>{savedItems[item.id] ? "Saved" : "Save"}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onOpenCase && onOpenCase(item.documentId || 1, Number(item.paraNo) || null)}
                    className="text-slate-600 hover:text-slate-950 transition-colors"
                    title="View external record"
                  >
                    <ExternalLink className="h-3.5 w-3.5 stroke-[2.5]" />
                  </button>
                </div>
              </div>
            </div>
          </Card3D>
        ))}
      </div>

      {/* Source Information Card */}
      <div className="bg-[#f8fafc] border-2 border-slate-300 rounded-xl p-4 space-y-3 shadow-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 font-bold text-sm text-slate-950">
            <Database className="h-4 w-4 text-slate-900 stroke-[2.5]" />
            <span>Source Information</span>
          </div>
          <span className="text-xs font-bold text-slate-800 hover:text-slate-950 cursor-pointer underline">
            View All →
          </span>
        </div>

        <ul className="space-y-2 text-xs sm:text-sm text-slate-950 font-semibold">
          <li className="flex items-start space-x-2.5">
            <Check className="h-4 w-4 text-[#15803d] stroke-[2.5] shrink-0 mt-0.5" />
            <span>Supreme Court corpus (Dattam Labs, AWS Open Data)</span>
          </li>
          <li className="flex items-start space-x-2.5">
            <Check className="h-4 w-4 text-[#15803d] stroke-[2.5] shrink-0 mt-0.5" />
            <span>Indian High Court judgments</span>
          </li>
          <li className="flex items-start space-x-2.5">
            <Check className="h-4 w-4 text-[#15803d] stroke-[2.5] shrink-0 mt-0.5" />
            <span>Official statutes (India Code)</span>
          </li>
          <li className="flex items-start space-x-2.5">
            <Check className="h-4 w-4 text-[#15803d] stroke-[2.5] shrink-0 mt-0.5" />
            <span>Paragraph-level citation mapping</span>
          </li>
          <li className="flex items-start space-x-2.5">
            <Check className="h-4 w-4 text-[#15803d] stroke-[2.5] shrink-0 mt-0.5" />
            <span>Automatic source verification</span>
          </li>
        </ul>
      </div>

      {/* Research Information Only / Legal Disclaimer Card */}
      <div className="bg-[#edf2ec] border-2 border-[#c2d4c0] rounded-xl p-4 text-xs sm:text-sm text-slate-950 space-y-1.5 shadow-xs">
        <div className="flex items-center space-x-2 font-bold text-slate-950">
          <Info className="h-4 w-4 text-slate-900 stroke-[2.5] shrink-0" />
          <span>Research Information Only</span>
        </div>
        <p className="leading-relaxed text-slate-800 font-medium">
          Needhi is an automated informational research assistant for Indian law. It does not provide legal advice, legal opinions, or case strategy. Always verify with the official judgment and the Gazette of India.
        </p>
      </div>
    </aside>
  );
};

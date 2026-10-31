import React from "react";

interface Props {
  text: string;
  onCitationClick?: (citationMarker: string) => void;
  className?: string;
}

export const LegalAnswerViewer: React.FC<Props> = ({
  text,
  onCitationClick,
  className = "",
}) => {
  if (!text) return null;

  // Helper to render text with bold, italics, and clickable citation badges
  const renderFormattedInline = (raw: string, keyPrefix: string) => {
    // Tokenize citations: [C1], [C2], [P12], [S1], etc.
    const citationRegex = /(\[C\d+\]|\[P\d+\]|\[S\d+\])/g;
    const segments = raw.split(citationRegex);

    return (
      <span key={keyPrefix}>
        {segments.map((seg, i) => {
          if (seg.match(/^\[(C|P|S)\d+\]$/)) {
            return (
              <button
                key={`${keyPrefix}-cite-${i}`}
                type="button"
                onClick={() => onCitationClick && onCitationClick(seg)}
                className="inline-flex items-center text-xs font-mono font-bold bg-[#fef3c7] hover:bg-[#fde68a] text-[#78350f] border border-[#f59e0b] rounded px-2 py-0.5 mx-1 transition-all hover:scale-105 cursor-pointer shadow-3xs"
                title={`View referenced authority ${seg}`}
              >
                {seg}
              </button>
            );
          }

          // Parse bold **text** within this segment
          const boldParts = seg.split(/(\*\*[^*]+\*\*)/g);
          return (
            <span key={`${keyPrefix}-txt-${i}`}>
              {boldParts.map((bPart, bIdx) => {
                if (bPart.startsWith("**") && bPart.endsWith("**")) {
                  const inner = bPart.slice(2, -2);
                  return (
                    <strong
                      key={`${keyPrefix}-b-${bIdx}`}
                      className="font-bold text-slate-950"
                    >
                      {inner}
                    </strong>
                  );
                }

                // Parse italic *text*
                const italicParts = bPart.split(/(\*[^*]+\*)/g);
                return italicParts.map((iPart, iIdx) => {
                  if (iPart.startsWith("*") && iPart.endsWith("*") && iPart.length > 2) {
                    return (
                      <em
                        key={`${keyPrefix}-em-${iIdx}`}
                        className="italic font-medium text-slate-900"
                      >
                        {iPart.slice(1, -1)}
                      </em>
                    );
                  }
                  return <span key={`${keyPrefix}-plain-${iIdx}`}>{iPart}</span>;
                });
              })}
            </span>
          );
        })}
      </span>
    );
  };

  // Split into paragraphs or bullet blocks
  const paragraphs = text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);

  let pointCounter = 1;

  return (
    <div className={`space-y-4 font-sans text-slate-950 leading-relaxed ${className}`}>
      {paragraphs.map((para, pIdx) => {
        // Check if paragraph contains bullet points like "* **Title:** description" or "- **Title:**"
        const bulletLines = para.split(/\n(?=[*-]\s+|\d+\.\s+)/);

        if (bulletLines.length > 1 || para.startsWith("* ") || para.startsWith("- ") || /^\d+\.\s+/.test(para)) {
          return (
            <div key={`p-${pIdx}`} className="space-y-3 pt-1">
              {bulletLines.map((line, lIdx) => {
                const cleanLine = line.replace(/^[*-]\s+|\d+\.\s+/, "").trim();
                const currentNumber = pointCounter++;

                // Check if line starts with **Title:**
                const titleMatch = cleanLine.match(/^\*\*([^*]+)\*\*[:\s]*(.*)/);
                if (titleMatch) {
                  const title = titleMatch[1];
                  const body = titleMatch[2];
                  return (
                    <div
                      key={`bullet-${lIdx}`}
                      className="flex items-start space-x-3.5 p-4 rounded-xl bg-slate-50 border-2 border-slate-200/90 shadow-3xs hover:border-slate-300 transition-colors"
                    >
                      <span className="w-8 h-8 rounded-full bg-[#dcfce7] text-[#14532d] border border-[#86efac] font-bold text-sm flex items-center justify-center shrink-0 mt-0.5 shadow-3xs">
                        {currentNumber}
                      </span>
                      <div className="space-y-1">
                        <h4 className="font-bold text-base text-slate-950">
                          {title}
                        </h4>
                        <p className="text-sm sm:text-base text-slate-900 font-medium leading-relaxed">
                          {renderFormattedInline(body, `b-${pIdx}-${lIdx}`)}
                        </p>
                      </div>
                    </div>
                  );
                }

                // Regular bullet item
                return (
                  <div
                    key={`bullet-${lIdx}`}
                    className="flex items-start space-x-3 p-3.5 rounded-xl bg-slate-50 border-2 border-slate-200/90 shadow-3xs"
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 mt-2 shrink-0"></span>
                    <p className="text-sm sm:text-base text-slate-900 font-medium leading-relaxed">
                      {renderFormattedInline(cleanLine, `bl-${pIdx}-${lIdx}`)}
                    </p>
                  </div>
                );
              })}
            </div>
          );
        }

        // Regular paragraph (like intro sentence)
        return (
          <p
            key={`p-${pIdx}`}
            className="text-base sm:text-lg text-slate-950 font-semibold leading-relaxed"
          >
            {renderFormattedInline(para, `p-${pIdx}`)}
          </p>
        );
      })}
    </div>
  );
};

export default LegalAnswerViewer;

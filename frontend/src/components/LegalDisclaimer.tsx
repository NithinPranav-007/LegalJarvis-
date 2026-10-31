import React from "react";
import { AlertTriangle } from "lucide-react";

export const LegalDisclaimer: React.FC<{ className?: string }> = ({ className = "" }) => {
  return (
    <aside
      aria-label="Legal Disclaimer"
      className={`bg-amber-50 border border-amber-200 text-amber-900 rounded-lg p-3 text-xs leading-relaxed flex items-start space-x-2.5 ${className}`}
    >
      <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
      <div>
        <strong className="font-semibold">Informational Research Notice:</strong> Needhi is an automated
        informational research assistant for Indian law. It does not provide legal advice, legal opinions, or case
        strategy, and does not create an advocate-client relationship. All citations and reasoning must be
        independently verified against official court transcripts and the Gazette of India before relying upon them in
        any court or proceeding.
      </div>
    </aside>
  );
};

export default LegalDisclaimer;

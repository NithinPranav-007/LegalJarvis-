import React, { useState } from "react";
import { ThumbsUp, ThumbsDown, CheckCircle2, MessageSquare } from "lucide-react";
import { api } from "../api/client";

interface Props {
  query?: string;
  answerId?: number | null;
}

type FeedbackLabel = "supported" | "unsupported" | "hallucinated" | "incomplete" | "wrong_law";

export const FeedbackWidget: React.FC<Props> = ({ query, answerId }) => {
  const [rating, setRating] = useState<number | null>(null);
  const [label, setLabel] = useState<FeedbackLabel | null>(null);
  const [notes, setNotes] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const handleRatingClick = async (val: number) => {
    setRating(val);
    setShowDetails(true);
    if (val === 1 && !notes) {
      // Auto-submit thumbs-up if user doesn't want extra comments
      try {
        await api.submitFeedback({
          answer_id: answerId,
          query,
          rating: 1,
          label: "supported",
        });
      } catch (e) {
        // Silent error for optional quick feedback
      }
    }
  };

  const handleSubmitDetailed = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === null) return;
    setSubmitting(true);
    try {
      await api.submitFeedback({
        answer_id: answerId,
        query,
        rating,
        label: label || (rating === 1 ? "supported" : "unsupported"),
        notes: notes.trim() || undefined,
      });
      setSubmitted(true);
    } catch (e) {
      // Mark as submitted locally so UI is responsive
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg flex items-center space-x-2 text-xs font-medium">
        <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
        <span>Thank you for your feedback! Your evaluation helps refine LegalJarvis verification.</span>
      </div>
    );
  }

  return (
    <div className="mt-5 pt-3 border-t border-slate-200 text-xs text-slate-600">
      <div className="flex items-center justify-between">
        <span className="font-medium text-slate-700">Was this answer accurate and well-grounded?</span>
        <div className="flex items-center space-x-2">
          <button
            type="button"
            aria-label="Thumbs up - answer is accurate"
            onClick={() => handleRatingClick(1)}
            className={`p-1.5 rounded-md border flex items-center space-x-1 transition-colors ${
              rating === 1
                ? "bg-emerald-100 border-emerald-400 text-emerald-800"
                : "border-slate-200 hover:bg-slate-100 text-slate-600"
            }`}
          >
            <ThumbsUp className="h-3.5 w-3.5" />
            <span className="text-[11px] font-medium">Yes</span>
          </button>
          <button
            type="button"
            aria-label="Thumbs down - answer has issues"
            onClick={() => handleRatingClick(-1)}
            className={`p-1.5 rounded-md border flex items-center space-x-1 transition-colors ${
              rating === -1
                ? "bg-rose-100 border-rose-400 text-rose-800"
                : "border-slate-200 hover:bg-slate-100 text-slate-600"
            }`}
          >
            <ThumbsDown className="h-3.5 w-3.5" />
            <span className="text-[11px] font-medium">No</span>
          </button>
        </div>
      </div>

      {showDetails && (
        <form onSubmit={handleSubmitDetailed} className="mt-3 bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-2">
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className="text-[11px] font-semibold text-slate-700 mr-1">Classification:</span>
            {(
              [
                ["supported", "Well Supported"],
                ["unsupported", "Unsupported Passage"],
                ["hallucinated", "Hallucinated Claim"],
                ["incomplete", "Incomplete Precedent"],
                ["wrong_law", "Outdated Law (IPC vs BNS)"],
              ] as const
            ).map(([val, text]) => (
              <button
                key={val}
                type="button"
                onClick={() => setLabel(val)}
                className={`text-[11px] px-2 py-0.5 rounded-full border transition-colors ${
                  label === val
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
                }`}
              >
                {text}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional notes or citation discrepancy..."
              className="flex-1 px-2.5 py-1 text-xs border border-slate-300 rounded bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={submitting}
              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white rounded text-[11px] font-medium flex items-center space-x-1"
            >
              <MessageSquare className="h-3 w-3" />
              <span>{submitting ? "Sending..." : "Submit Review"}</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default FeedbackWidget;

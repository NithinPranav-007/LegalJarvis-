import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { HistoryPage } from "../../src/pages/History";
import { FeedbackWidget } from "../../src/components/FeedbackWidget";
import { api } from "../../src/api/client";

vi.mock("../../src/api/client", () => ({
  api: {
    submitFeedback: vi.fn(),
  },
}));

describe("HistoryPage & FeedbackWidget Components (PRD T-14)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("HistoryPage: renders previous queries from localStorage and supports Re-Ask", () => {
    const mockHistory = [
      {
        id: "1",
        timestamp: "2026-10-28T10:00:00.000Z",
        query: "What are the elements of criminal conspiracy?",
        answer: "Criminal conspiracy requires agreement between two or more persons under Section 120A IPC.",
        abstained: false,
        citationsCount: 2,
      },
    ];
    localStorage.setItem("legaljarvis_history", JSON.stringify(mockHistory));

    const onReAskMock = vi.fn();
    render(<HistoryPage onReAsk={onReAskMock} />);

    expect(screen.getByText("What are the elements of criminal conspiracy?")).toBeInTheDocument();
    expect(screen.getByText(/2 citations referenced/i)).toBeInTheDocument();

    const reAskBtn = screen.getByRole("button", { name: /Re-Ask/i });
    fireEvent.click(reAskBtn);
    expect(onReAskMock).toHaveBeenCalledWith("What are the elements of criminal conspiracy?");
  });

  it("HistoryPage: displays empty state when localStorage has no queries", () => {
    render(<HistoryPage onReAsk={vi.fn()} />);
    expect(screen.getByText(/No Query History Yet/i)).toBeInTheDocument();
  });

  it("FeedbackWidget: captures thumbs up and submits rating", async () => {
    (api.submitFeedback as any).mockResolvedValue({ id: 1, status: "success", message: "Recorded" });

    render(<FeedbackWidget query="Test legal inquiry" answerId={10} />);

    const thumbsUp = screen.getByRole("button", { name: /Thumbs up/i });
    fireEvent.click(thumbsUp);

    expect(api.submitFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        answer_id: 10,
        query: "Test legal inquiry",
        rating: 1,
        label: "supported",
      })
    );
  });

  it("FeedbackWidget: allows classification label and comment submission", async () => {
    (api.submitFeedback as any).mockResolvedValue({ id: 1, status: "success", message: "Recorded" });

    render(<FeedbackWidget query="Test legal inquiry" answerId={10} />);

    const thumbsDown = screen.getByRole("button", { name: /Thumbs down/i });
    fireEvent.click(thumbsDown);

    // Select label 'Hallucinated Claim'
    const labelBtn = screen.getByRole("button", { name: /Hallucinated Claim/i });
    fireEvent.click(labelBtn);

    // Enter notes
    const input = screen.getByPlaceholderText(/Optional notes/i);
    fireEvent.change(input, { target: { value: "Section 302 cited incorrectly" } });

    // Submit review
    const submitBtn = screen.getByRole("button", { name: /Submit Review/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.submitFeedback).toHaveBeenCalledWith(
        expect.objectContaining({
          rating: -1,
          label: "hallucinated",
          notes: "Section 302 cited incorrectly",
        })
      );
      expect(screen.getByText(/Thank you for your feedback!/i)).toBeInTheDocument();
    });
  });
});

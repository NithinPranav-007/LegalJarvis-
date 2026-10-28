import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AskPage } from "../../src/pages/Ask";
import { api } from "../../src/api/client";

vi.mock("../../src/api/client", () => ({
  api: {
    ask: vi.fn(),
    submitFeedback: vi.fn(),
  },
}));

describe("AskPage State Requirements (PRD T-14)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("1. Empty State: renders welcoming interface and sample inquiries on initial load", () => {
    render(<AskPage />);
    expect(
      screen.getByText(/Citation-Verified Legal Q&A/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Sample Indian Legal Inquiries/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/essential ingredients of criminal conspiracy/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Ask LegalJarvis/i })
    ).toBeDisabled();
  });

  it("2. Loading State: displays progress indicator and accessible status while analyzing", async () => {
    // Return a pending promise that doesn't resolve immediately
    (api.ask as any).mockImplementation(() => new Promise(() => {}));

    render(<AskPage initialQuery="What is anticipatory bail?" />);
    const submitBtn = screen.getByRole("button", { name: /Ask LegalJarvis/i });
    expect(submitBtn).toBeEnabled();

    fireEvent.click(submitBtn);

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(
      screen.getByText(/Retrieving Authoritative Passages/i)
    ).toBeInTheDocument();
  });

  it("3. Abstain State: displays low-evidence warning when confidence/citations fall below threshold", async () => {
    (api.ask as any).mockResolvedValue({
      question: "What is an alien treaty clause in 1800?",
      answer: "LegalJarvis could not find sufficient authoritative Indian case law.",
      citations: [],
      abstained: true,
      abstention_reason:
        "No Supreme Court precedent met the required citation support threshold (60%+ keyword support).",
      disclaimer: "Informational only.",
      generation_status: "abstained",
    });

    render(<AskPage initialQuery="What is an alien treaty clause in 1800?" />);
    const submitBtn = screen.getByRole("button", { name: /Ask LegalJarvis/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByRole("alert", { name: /Low Evidence Abstention/i })
      ).toBeInTheDocument();
      expect(
        screen.getByText(/could not find sufficient authoritative Indian case law/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/threshold \(60%\+ keyword support\)/i)
      ).toBeInTheDocument();
    });
  });

  it("4. Error State: displays error banner and allows retry when network/server fails", async () => {
    (api.ask as any).mockRejectedValue(new Error("Connection refused to LegalJarvis backend"));

    render(<AskPage initialQuery="Right to privacy Article 21" />);
    fireEvent.click(screen.getByRole("button", { name: /Ask LegalJarvis/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/Unable to Complete Request/i)).toBeInTheDocument();
      expect(screen.getByText(/Connection refused to LegalJarvis backend/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Retry Query/i })).toBeInTheDocument();
    });
  });

  it("5. Success State: renders grounded answer, transition notice, citation cards, and triggers citation click", async () => {
    const onNavigateMock = vi.fn();
    (api.ask as any).mockResolvedValue({
      question: "What is the test for anticipatory bail under CrPC 438?",
      answer:
        "Anticipatory bail is governed by principles laid down in Gurbaksh Singh Sibbia [C1]. The power under Section 438 is of wide amplitude [C2].",
      citations: [
        {
          marker: "[C1]",
          chunk_id: 101,
          document_id: 1,
          title: "Gurbaksh Singh Sibbia v. State of Punjab",
          court: "Supreme Court of India",
          neutral_citation: "1980 INSC 77",
          para_no: 12,
          snippet: "Section 438 of the Code confers a wide power to grant anticipatory bail.",
          attribution: "Open Government Data / CC-BY 4.0",
        },
        {
          marker: "[C2]",
          chunk_id: 102,
          document_id: 1,
          title: "Gurbaksh Singh Sibbia v. State of Punjab",
          court: "Supreme Court of India",
          neutral_citation: "1980 INSC 77",
          para_no: 14,
          snippet: "The power should not be circumscribed by rigid rules not present in the statute.",
          attribution: "Open Government Data / CC-BY 4.0",
        },
      ],
      abstained: false,
      criminal_transition_notice:
        "Statutory Transition: CrPC 438 is now replaced by Section 482 of Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023.",
      disclaimer: "Informational only.",
      generation_status: "completed",
    });

    render(
      <AskPage
        initialQuery="What is the test for anticipatory bail under CrPC 438?"
        onNavigateToCase={onNavigateMock}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Ask LegalJarvis/i }));

    await waitFor(() => {
      expect(screen.getByText(/Verified Answer/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Gurbaksh Singh Sibbia/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/Statutory Transition/i)).toBeInTheDocument();
    });

    // Check inline citation pills exist
    const citationPills = screen.getAllByRole("button", { name: /\[C1\]/i });
    expect(citationPills.length).toBeGreaterThanOrEqual(1);

    // Clicking [C1] triggers onNavigateToCase with documentId 1 and paraNo 12
    fireEvent.click(citationPills[0]);
    expect(onNavigateMock).toHaveBeenCalledWith(1, 12);
  });
});

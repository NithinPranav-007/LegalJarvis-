import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { CaseViewerPage } from "../../src/pages/CaseViewer";
import { api } from "../../src/api/client";

vi.mock("../../src/api/client", () => ({
  api: {
    getDocument: vi.fn(),
    listDocuments: vi.fn(),
  },
}));

describe("CaseViewerPage Component (PRD T-14)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockDoc = {
    id: 1,
    title: "Gurbaksh Singh Sibbia v. State of Punjab",
    court_code: "sc",
    court_name: "Supreme Court of India",
    decision_date: "1980-04-09",
    neutral_citation: "1980 INSC 77",
    bench: "Y.V. Chandrachud, P.N. Bhagwati, V.R. Krishna Iyer",
    dataset_name: "sc_2023",
    text: "Full text of the judgment...",
    chunks: [
      {
        id: 101,
        para_no: 12,
        segment_type: "facts",
        text: "Section 438 of the Code of Criminal Procedure confers wide discretion on the High Court and Court of Session.",
        start_char: 0,
        end_char: 110,
      },
      {
        id: 102,
        para_no: 14,
        segment_type: "holding",
        text: "The High Court or Court of Session has power to grant anticipatory bail without unnecessary legislative shackles.",
        start_char: 112,
        end_char: 228,
      },
    ],
    attribution: "Open Government Data (OGD) / Creative Commons Attribution (CC-BY 4.0)",
  };

  it("renders judgment metadata, bench, citation, and paragraphs", async () => {
    (api.listDocuments as any).mockResolvedValue([
      { id: 1, title: "Gurbaksh Singh Sibbia v. State of Punjab", court_code: "sc", neutral_citation: "1980 INSC 77" },
    ]);
    (api.getDocument as any).mockResolvedValue(mockDoc);

    render(<CaseViewerPage documentId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Gurbaksh Singh Sibbia v. State of Punjab")).toBeInTheDocument();
      expect(screen.getAllByText("1980 INSC 77").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("1980-04-09").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/Y.V. Chandrachud/i)).toBeInTheDocument();
      expect(screen.getByText(/¶ 12/)).toBeInTheDocument();
      expect(screen.getByText(/¶ 14/)).toBeInTheDocument();
      expect(screen.getByText(/Open Government Data/i)).toBeInTheDocument();
    });
  });

  it("highlights the exact cited paragraph when highlightParaNo is provided", async () => {
    (api.listDocuments as any).mockResolvedValue([]);
    (api.getDocument as any).mockResolvedValue(mockDoc);

    render(<CaseViewerPage documentId={1} highlightParaNo={14} />);

    await waitFor(() => {
      expect(screen.getByText("Cited Paragraph")).toBeInTheDocument();
      const para14 = document.getElementById("para-14");
      expect(para14).toBeInTheDocument();
      expect(para14).toHaveClass("border-amber-400");
    });
  });

  it("filters paragraphs by rhetorical role (e.g. holding)", async () => {
    (api.listDocuments as any).mockResolvedValue([]);
    (api.getDocument as any).mockResolvedValue(mockDoc);

    render(<CaseViewerPage documentId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/¶ 12/)).toBeInTheDocument();
      expect(screen.getByText(/¶ 14/)).toBeInTheDocument();
    });

    // Click 'holding' filter button
    const holdingFilter = screen.getByRole("button", { name: "holding" });
    fireEvent.click(holdingFilter);

    expect(screen.getByText(/¶ 14/)).toBeInTheDocument();
    expect(screen.queryByText(/¶ 12/)).not.toBeInTheDocument();
  });
});

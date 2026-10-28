import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("LegalJarvis E2E Tests (PRD T-14)", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to local dev server
    await page.goto("/");
  });

  test("1. Empty state & initial landing: verifies header, sample questions, and disclaimer @a11y", async ({
    page,
  }) => {
    await expect(page.locator("h1, h2").first()).toContainText("LegalJarvis");
    await expect(page.getByText("Citation-Verified Legal Q&A")).toBeVisible();
    await expect(page.getByText("Sample Indian Legal Inquiries")).toBeVisible();
    await expect(page.locator("aside[aria-label='Legal Disclaimer']")).toBeVisible();
    await expect(page.getByRole("button", { name: /Ask LegalJarvis/i })).toBeDisabled();
  });

  test("2. Tab navigation: switches between Ask, Search, Case Viewer, and History @a11y", async ({
    page,
  }) => {
    // Navigate to Search
    await page.getByRole("button", { name: "Search" }).click();
    await expect(page.getByText("Indian Case Law & Precedent Search")).toBeVisible();

    // Navigate to Case Viewer
    await page.getByRole("button", { name: "Case Viewer" }).click();
    await expect(page.getByText("Indian Case Law Reader")).toBeVisible();

    // Navigate to History
    await page.getByRole("button", { name: "History" }).click();
    await expect(page.getByText("Research Query History")).toBeVisible();

    // Back to Ask
    await page.getByRole("button", { name: "Ask Q&A" }).click();
    await expect(page.getByText("Citation-Verified Legal Q&A")).toBeVisible();
  });

  test("3. Ask Question flow & Loading state: routes query and shows progress indicator", async ({
    page,
  }) => {
    // Intercept /v1/qa endpoint to test loading state
    await page.route("**/v1/qa", async (route) => {
      // delay response by 500ms
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          question: "What are the ingredients of Section 120A IPC?",
          answer: "Criminal conspiracy requires agreement between two persons [C1].",
          citations: [
            {
              marker: "[C1]",
              chunk_id: 1,
              document_id: 1,
              title: "State v. Nalini",
              court: "Supreme Court of India",
              neutral_citation: "1999 INSC 220",
              para_no: 15,
              snippet: "The agreement is the crux of the offence under Section 120A.",
              attribution: "Open Government Data / CC-BY 4.0",
            },
          ],
          abstained: false,
          disclaimer: "Informational only.",
          generation_status: "completed",
        }),
      });
    });

    const textarea = page.getByPlaceholder("Ask a question on Indian case law");
    await textarea.fill("What are the ingredients of Section 120A IPC?");
    const submitBtn = page.getByRole("button", { name: /Ask LegalJarvis/i });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Check loading indicator appears
    await expect(page.locator("div[role='status']")).toBeVisible();

    // Check success answer appears
    await expect(page.getByText("Verified Answer")).toBeVisible();
    await expect(page.getByRole("button", { name: "[C1]" })).toBeVisible();
  });

  test("4. Abstain state: displays safety low-evidence banner when query cannot be verified", async ({
    page,
  }) => {
    await page.route("**/v1/qa", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          question: "Ancient extraterrestrial treaty law?",
          answer: "LegalJarvis could not find sufficient authoritative Indian case law.",
          citations: [],
          abstained: true,
          abstention_reason: "Precedent passages did not meet the required citation support threshold.",
          disclaimer: "Informational only.",
          generation_status: "abstained",
        }),
      });
    });

    const textarea = page.getByPlaceholder("Ask a question on Indian case law");
    await textarea.fill("Ancient extraterrestrial treaty law?");
    await page.getByRole("button", { name: /Ask LegalJarvis/i }).click();

    await expect(page.locator("div[role='alert'][aria-label='Low Evidence Abstention']")).toBeVisible();
    await expect(page.getByText("could not find sufficient authoritative Indian case law")).toBeVisible();
  });

  test("5. Error state: displays error alert and retry button when backend fails", async ({
    page,
  }) => {
    await page.route("**/v1/qa", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Database connection failed" }),
      });
    });

    const textarea = page.getByPlaceholder("Ask a question on Indian case law");
    await textarea.fill("Valid legal inquiry test?");
    await page.getByRole("button", { name: /Ask LegalJarvis/i }).click();

    await expect(page.locator("div[role='alert']")).toBeVisible();
    await expect(page.getByText("Unable to Complete Request")).toBeVisible();
    await expect(page.getByRole("button", { name: /Retry Query/i })).toBeVisible();
  });

  test("6. Citation click highlights exact paragraph: clicking [C1] navigates to Case Viewer and highlights #para-15", async ({
    page,
  }) => {
    // Mock /v1/qa
    await page.route("**/v1/qa", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          question: "Conspiracy law in India",
          answer: "Agreement is required [C1].",
          citations: [
            {
              marker: "[C1]",
              chunk_id: 101,
              document_id: 42,
              title: "State of Maharashtra v. Som Nath Thapa",
              court: "Supreme Court of India",
              neutral_citation: "1996 INSC 450",
              para_no: 15,
              snippet: "For establishing a charge of conspiracy knowledge is essential.",
              attribution: "Open Government Data / CC-BY 4.0",
            },
          ],
          abstained: false,
          disclaimer: "Informational only.",
          generation_status: "completed",
        }),
      });
    });

    // Mock /v1/documents/42
    await page.route("**/v1/documents/42", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 42,
          title: "State of Maharashtra v. Som Nath Thapa",
          court_code: "sc",
          court_name: "Supreme Court of India",
          decision_date: "1996-04-12",
          neutral_citation: "1996 INSC 450",
          bench: "K. Ramaswamy, G.B. Pattanaik",
          dataset_name: "sc_2023",
          text: "Full text...",
          chunks: [
            {
              id: 100,
              para_no: 14,
              segment_type: "facts",
              text: "The prosecution alleged conspiracy under Section 120B.",
              start_char: 0,
              end_char: 50,
            },
            {
              id: 101,
              para_no: 15,
              segment_type: "reasoning",
              text: "For establishing a charge of conspiracy knowledge is essential.",
              start_char: 51,
              end_char: 120,
            },
          ],
          attribution: "Open Government Data (OGD) / CC-BY 4.0",
        }),
      });
    });

    // Submit question
    const textarea = page.getByPlaceholder("Ask a question on Indian case law");
    await textarea.fill("Conspiracy law in India");
    await page.getByRole("button", { name: /Ask LegalJarvis/i }).click();

    // Wait for answer
    await expect(page.getByText("Verified Answer")).toBeVisible();

    // Click [C1] marker
    const citationBtn = page.getByRole("button", { name: "[C1]" });
    await expect(citationBtn).toBeVisible();
    await citationBtn.click();

    // Verify it navigated to Case Viewer and highlighted para 15
    await expect(page.getByText("Indian Case Law Reader")).toBeVisible();
    await expect(page.getByText("State of Maharashtra v. Som Nath Thapa")).toBeVisible();
    await expect(page.getByText("Cited Paragraph")).toBeVisible();

    const para15 = page.locator("#para-15");
    await expect(para15).toBeVisible();
    await expect(para15).toContainText("¶ 15");
    await expect(para15).toContainText("For establishing a charge of conspiracy");
  });

  test("7. Accessibility verification @a11y: checks ARIA landmarks, roles, and focusability", async ({
    page,
  }) => {
    // Landmark roles
    await expect(page.locator("header")).toBeVisible();
    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("footer")).toBeVisible();
    await expect(page.locator("nav[aria-label='Main Navigation']")).toBeVisible();
    await expect(page.locator("aside[aria-label='Legal Disclaimer']")).toBeVisible();

    // Tab buttons are interactive
    const askTab = page.getByRole("button", { name: "Ask Q&A" });
    const searchTab = page.getByRole("button", { name: "Search" });
    await expect(askTab).toBeEnabled();
    await expect(searchTab).toBeEnabled();
  });

  test("8. Automated WCAG 2.1 AA audit with axe-core across core pages @a11y", async ({
    page,
  }) => {
    // 1. Landing / Ask Q&A page
    await page.goto("/");
    const askAxe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    const criticalAsk = askAxe.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );
    expect(criticalAsk).toEqual([]);

    // 2. Search page
    await page.getByRole("button", { name: "Search" }).click();
    const searchAxe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    const criticalSearch = searchAxe.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );
    expect(criticalSearch).toEqual([]);

    // 3. Case Viewer page
    await page.getByRole("button", { name: "Case Viewer" }).click();
    const viewerAxe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    const criticalViewer = viewerAxe.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );
    expect(criticalViewer).toEqual([]);

    // 4. History page
    await page.getByRole("button", { name: "History" }).click();
    const historyAxe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    const criticalHistory = historyAxe.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );
    expect(criticalHistory).toEqual([]);

    // 5. Reviewer Portal page
    await page.getByRole("button", { name: "Reviewer" }).click();
    const reviewerAxe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    const criticalReviewer = reviewerAxe.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );
    expect(criticalReviewer).toEqual([]);
  });
});

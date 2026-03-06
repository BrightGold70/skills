import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { PipelineMonitor } from "./PipelineMonitor";

// Mock useApi
vi.mock("../hooks/useApi", () => ({
  api: vi.fn(),
}));

import { api } from "../hooks/useApi";
const mockApi = vi.mocked(api);

describe("PipelineMonitor", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders pipeline steps in pending state", () => {
    render(<PipelineMonitor />);
    expect(screen.getByText("CRF Pipeline Monitor")).toBeTruthy();
    expect(screen.getByText("Extract")).toBeTruthy();
    expect(screen.getByText("Validate")).toBeTruthy();
    expect(screen.getByText("Analyze")).toBeTruthy();
    expect(screen.getByText("Report")).toBeTruthy();
  });

  it("has a Run Pipeline button", () => {
    render(<PipelineMonitor />);
    expect(screen.getByRole("button", { name: /run pipeline/i })).toBeTruthy();
  });

  it("shows running state during API call", async () => {
    let resolveApi: (v: unknown) => void;
    mockApi.mockImplementation(
      () => new Promise((resolve) => { resolveApi = resolve; })
    );
    render(<PipelineMonitor />);
    fireEvent.click(screen.getByRole("button", { name: /run pipeline/i }));
    await waitFor(() => {
      expect(screen.getByText("Running pipeline...")).toBeTruthy();
    });
    // Clean up: resolve the pending promise
    resolveApi!({ steps: [] });
  });

  it("displays step results after completion", async () => {
    mockApi.mockResolvedValue({
      steps: [
        { step: "extract", status: "done", output: "Extracted 100 records", duration_ms: 800 },
        { step: "validate", status: "done", output: "All valid", duration_ms: 1200 },
        { step: "analyze", status: "done", output: "Analysis complete", duration_ms: 2000 },
        { step: "report", status: "done", output: "Report generated", duration_ms: 500 },
      ],
    });

    render(<PipelineMonitor />);
    fireEvent.click(screen.getByRole("button", { name: /run pipeline/i }));

    await waitFor(() => {
      // Step results appear as truncated text in step rows
      expect(screen.getByText("Extracted 100 records")).toBeTruthy();
    });
  });

  it("handles error state", async () => {
    mockApi.mockRejectedValue(new Error("Pipeline failed"));
    render(<PipelineMonitor />);
    fireEvent.click(screen.getByRole("button", { name: /run pipeline/i }));

    await waitFor(() => {
      expect(screen.getByText(/pipeline failed/i)).toBeTruthy();
    });
  });
});

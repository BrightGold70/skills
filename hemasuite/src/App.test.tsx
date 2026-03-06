import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";

// Mock the health hook
vi.mock("./hooks/useSidecarHealth", () => ({
  useSidecarHealth: vi.fn(),
}));

import { useSidecarHealth } from "./hooks/useSidecarHealth";
const mockUseSidecarHealth = vi.mocked(useSidecarHealth);

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

describe("App", () => {
  beforeEach(() => {
    Object.defineProperty(globalThis, "localStorage", { value: localStorageMock, writable: true });
    localStorageMock.clear();
    // Dismiss first-launch dialog by default so existing tests aren't affected
    localStorageMock.setItem("hemasuite-first-launch-dismissed", "true");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows splash screen when sidecar is not ready", () => {
    mockUseSidecarHealth.mockReturnValue({ ready: false });
    render(<App />);
    expect(screen.getByText("HemaSuite")).toBeInTheDocument();
    expect(screen.getByText("Starting up...")).toBeInTheDocument();
  });

  it("shows main layout when sidecar is ready", () => {
    mockUseSidecarHealth.mockReturnValue({ ready: true });
    render(<App />);
    // MainLayout has tab buttons
    expect(screen.getByText("HPW")).toBeInTheDocument();
    expect(screen.getByText("CSA")).toBeInTheDocument();
  });

  it("transitions from splash to main layout", async () => {
    mockUseSidecarHealth
      .mockReturnValueOnce({ ready: false })
      .mockReturnValue({ ready: true });

    const { rerender } = render(<App />);
    expect(screen.getByText("Starting up...")).toBeInTheDocument();

    rerender(<App />);
    await waitFor(() => {
      expect(screen.getByText("HPW")).toBeInTheDocument();
    });
    expect(screen.queryByText("Starting up...")).not.toBeInTheDocument();
  });
});

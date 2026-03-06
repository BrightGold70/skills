import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useSidecarHealth } from "./useSidecarHealth";

describe("useSidecarHealth", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("starts with ready=false", () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("not up"));
    const { result } = renderHook(() => useSidecarHealth());
    expect(result.current.ready).toBe(false);
  });

  it("becomes ready when /health responds ok", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    );
    const { result } = renderHook(() => useSidecarHealth());

    await waitFor(() => {
      expect(result.current.ready).toBe(true);
    });
  });

  it("retries when /health fails then succeeds", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("not up"))
      .mockRejectedValueOnce(new Error("not up"))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
      );

    const { result } = renderHook(() => useSidecarHealth(100));

    // Wait for retries to resolve
    await waitFor(() => {
      expect(result.current.ready).toBe(true);
    });

    expect(fetchSpy).toHaveBeenCalledTimes(3);
  });

  it("stops polling once ready", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    );

    renderHook(() => useSidecarHealth(100));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    // Advance time well past another poll interval
    await vi.advanceTimersByTimeAsync(500);
    // Should still be 1 — no additional calls after becoming ready
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});

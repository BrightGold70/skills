import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";

// Mock @tauri-apps/api
vi.mock("@tauri-apps/api/event", () => ({
  listen: vi.fn(),
}));

import { listen } from "@tauri-apps/api/event";
const mockListen = vi.mocked(listen);

import { useMenuEvents } from "./useMenuEvents";

describe("useMenuEvents", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("registers a listener for menu events on mount", () => {
    const unlisten = vi.fn();
    mockListen.mockResolvedValue(unlisten);

    const handlers = { onNewProject: vi.fn(), onOpenProject: vi.fn(), onSave: vi.fn() };
    renderHook(() => useMenuEvents(handlers));

    expect(mockListen).toHaveBeenCalledWith("menu-event", expect.any(Function));
  });

  it("calls onNewProject when new-project event fires", async () => {
    let capturedCallback: ((event: unknown) => void) | undefined;
    mockListen.mockImplementation(async (_event, cb) => {
      capturedCallback = cb as (event: unknown) => void;
      return vi.fn();
    });

    const handlers = { onNewProject: vi.fn(), onOpenProject: vi.fn(), onSave: vi.fn() };
    renderHook(() => useMenuEvents(handlers));

    capturedCallback?.({ payload: "new-project", id: 0, event: "menu-event" });
    expect(handlers.onNewProject).toHaveBeenCalledTimes(1);
  });

  it("calls onOpenProject when open-project event fires", async () => {
    let capturedCallback: ((event: unknown) => void) | undefined;
    mockListen.mockImplementation(async (_event, cb) => {
      capturedCallback = cb as (event: unknown) => void;
      return vi.fn();
    });

    const handlers = { onNewProject: vi.fn(), onOpenProject: vi.fn(), onSave: vi.fn() };
    renderHook(() => useMenuEvents(handlers));

    capturedCallback?.({ payload: "open-project", id: 0, event: "menu-event" });
    expect(handlers.onOpenProject).toHaveBeenCalledTimes(1);
  });

  it("calls onSave when save event fires", async () => {
    let capturedCallback: ((event: unknown) => void) | undefined;
    mockListen.mockImplementation(async (_event, cb) => {
      capturedCallback = cb as (event: unknown) => void;
      return vi.fn();
    });

    const handlers = { onNewProject: vi.fn(), onOpenProject: vi.fn(), onSave: vi.fn() };
    renderHook(() => useMenuEvents(handlers));

    capturedCallback?.({ payload: "save", id: 0, event: "menu-event" });
    expect(handlers.onSave).toHaveBeenCalledTimes(1);
  });

  it("cleans up listener on unmount", async () => {
    const unlisten = vi.fn();
    mockListen.mockResolvedValue(unlisten);

    const handlers = { onNewProject: vi.fn(), onOpenProject: vi.fn(), onSave: vi.fn() };
    const { unmount } = renderHook(() => useMenuEvents(handlers));

    unmount();

    // Give the async cleanup time to resolve
    await vi.waitFor(() => {
      expect(unlisten).toHaveBeenCalled();
    });
  });
});

/**
 * Auto-Update Configuration Tests (Task 5.4)
 *
 * TDD: Validate that Tauri updater plugin is properly configured
 * for automatic app updates.
 */
import { describe, it, expect } from "vitest";
import tauriConfig from "../../src-tauri/tauri.conf.json";

describe("Auto-Update Configuration", () => {
  it("should have updater plugin configured", () => {
    const config = tauriConfig as Record<string, unknown>;
    const plugins = config.plugins as Record<string, unknown> | undefined;
    expect(plugins).toBeDefined();
    expect(plugins?.updater).toBeDefined();
  });

  it("should have updater endpoints defined", () => {
    const config = tauriConfig as Record<string, unknown>;
    const plugins = config.plugins as Record<string, unknown>;
    const updater = plugins.updater as Record<string, unknown>;
    expect(updater.endpoints).toBeDefined();
    const endpoints = updater.endpoints as string[];
    expect(endpoints.length).toBeGreaterThan(0);
  });

  it("should use pubkey for update verification", () => {
    const config = tauriConfig as Record<string, unknown>;
    const plugins = config.plugins as Record<string, unknown>;
    const updater = plugins.updater as Record<string, unknown>;
    expect(updater.pubkey).toBeDefined();
    expect(typeof updater.pubkey).toBe("string");
    expect((updater.pubkey as string).length).toBeGreaterThan(0);
  });
});

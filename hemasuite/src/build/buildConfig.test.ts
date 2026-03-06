/**
 * Build Configuration Validation Tests (Task 5.1)
 *
 * TDD: These tests define what a correct DMG build configuration looks like.
 * They validate tauri.conf.json has proper settings for macOS distribution.
 */
import { describe, it, expect } from "vitest";
import tauriConfig from "../../src-tauri/tauri.conf.json";

describe("Tauri Build Configuration for DMG", () => {
  describe("bundle settings", () => {
    it("should include bundled Python runtime in resources", () => {
      const resources = tauriConfig.bundle.resources;
      const hasPython = resources.some(
        (r: string) => r.includes("python") || r.includes("resources/python/**")
      );
      expect(hasPython).toBe(true);
    });

    it("should include bundled R runtime in resources", () => {
      const resources = tauriConfig.bundle.resources;
      const hasR = resources.some(
        (r: string) =>
          r.includes("r-runtime") || r.includes("resources/r-runtime/**")
      );
      expect(hasR).toBe(true);
    });

    it("should include sidecar Python files in resources", () => {
      const resources = tauriConfig.bundle.resources;
      const hasSidecar = resources.some((r: string) =>
        r.includes("sidecar")
      );
      expect(hasSidecar).toBe(true);
    });

    it("should target DMG for macOS", () => {
      const targets = tauriConfig.bundle.targets;
      // "all" includes DMG, or explicit "dmg" target
      const isDmgTarget =
        targets === "all" ||
        (Array.isArray(targets) && targets.includes("dmg"));
      expect(isDmgTarget).toBe(true);
    });

    it("should have macOS-specific bundle config", () => {
      const bundle = tauriConfig.bundle as Record<string, unknown>;
      const macOS = bundle.macOS as Record<string, unknown> | undefined;
      expect(macOS).toBeDefined();
      expect(macOS?.entitlements).toBeDefined();
      expect(macOS?.minimumSystemVersion).toBeDefined();
    });

    it("should have a proper app identifier", () => {
      expect(tauriConfig.identifier).toMatch(/^com\.\w+\.\w+$/);
    });
  });

  describe("app metadata", () => {
    it("should have a proper product name", () => {
      expect(tauriConfig.productName).toBe("HemaSuite");
    });

    it("should have version set", () => {
      expect(tauriConfig.version).toMatch(/^\d+\.\d+\.\d+$/);
    });
  });
});

import { describe, it, expect, beforeEach } from "vitest";
import { useProjectStore } from "./projectStore";

describe("projectStore", () => {
  beforeEach(() => {
    // Reset store to defaults between tests
    useProjectStore.setState({
      activeProject: null,
      activeTab: "hpw",
      activePhase: 0,
    });
  });

  it("initializes with default state", () => {
    const state = useProjectStore.getState();
    expect(state.activeProject).toBeNull();
    expect(state.activeTab).toBe("hpw");
    expect(state.activePhase).toBe(0);
  });

  it("setProject updates activeProject", () => {
    useProjectStore.getState().setProject("proj-1");
    expect(useProjectStore.getState().activeProject).toBe("proj-1");
  });

  it("setProject to null clears project", () => {
    useProjectStore.getState().setProject("proj-1");
    useProjectStore.getState().setProject(null);
    expect(useProjectStore.getState().activeProject).toBeNull();
  });

  it("setTab updates activeTab", () => {
    useProjectStore.getState().setTab("csa");
    expect(useProjectStore.getState().activeTab).toBe("csa");
  });

  it("setPhase updates activePhase", () => {
    useProjectStore.getState().setPhase(3);
    expect(useProjectStore.getState().activePhase).toBe(3);
  });

  it("state changes are independent", () => {
    useProjectStore.getState().setProject("proj-2");
    useProjectStore.getState().setTab("pipeline");
    useProjectStore.getState().setPhase(5);

    const state = useProjectStore.getState();
    expect(state.activeProject).toBe("proj-2");
    expect(state.activeTab).toBe("pipeline");
    expect(state.activePhase).toBe(5);
  });
});

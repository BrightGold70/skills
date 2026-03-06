import { create } from "zustand";

export type Tab = "projects" | "hpw" | "csa" | "pipeline" | "settings";

interface ProjectState {
  activeProject: string | null;
  activeTab: Tab;
  activePhase: number;
  setProject: (id: string | null) => void;
  setTab: (tab: Tab) => void;
  setPhase: (phase: number) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  activeProject: null,
  activeTab: "hpw",
  activePhase: 0,
  setProject: (id) => set({ activeProject: id }),
  setTab: (tab) => set({ activeTab: tab }),
  setPhase: (phase) => set({ activePhase: phase }),
}));

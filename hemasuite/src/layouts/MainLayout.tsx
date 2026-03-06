import { useState } from "react";
import { Sidebar } from "../components/Sidebar";
import { HpwEditor } from "../views/HpwEditor";
import { CsaDashboard } from "../views/CsaDashboard";
import { ProjectManager } from "../views/ProjectManager";
import { SettingsView } from "../views/SettingsView";

type Tab = "projects" | "hpw" | "csa" | "pipeline" | "settings";

export function MainLayout() {
  const [activeTab, setActiveTab] = useState<Tab>("hpw");
  const [activePhase, setActivePhase] = useState(0);

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar activePhase={activePhase} onPhaseSelect={setActivePhase} />
      <main className="flex-1 flex flex-col">
        <nav className="flex border-b bg-white px-4">
          {(["projects", "hpw", "csa", "pipeline", "settings"] as Tab[]).map((tab) => {
            const labels: Record<Tab, string> = {
              projects: "Projects",
              hpw: "HPW",
              csa: "CSA",
              pipeline: "Pipeline",
              settings: "Settings",
            };
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                {labels[tab]}
              </button>
            );
          })}
        </nav>
        <div className="flex-1 overflow-auto p-4">
          {activeTab === "projects" && <ProjectManager />}
          {activeTab === "hpw" && <HpwEditor />}
          {activeTab === "csa" && <CsaDashboard />}
          {activeTab === "pipeline" && (
            <div className="text-gray-500">Pipeline Monitor (coming soon)</div>
          )}
          {activeTab === "settings" && <SettingsView />}
        </div>
      </main>
    </div>
  );
}

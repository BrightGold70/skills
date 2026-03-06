const PHASES = [
  "Topic Development",
  "Research",
  "Journal Selection",
  "Drafting",
  "Quality",
  "References",
  "Prose & Style",
  "Peer Review",
  "Publication",
  "Resubmission",
];

interface SidebarProps {
  activePhase: number;
  onPhaseSelect: (index: number) => void;
}

export function Sidebar({ activePhase, onPhaseSelect }: SidebarProps) {
  return (
    <aside className="w-56 bg-slate-900 text-white flex flex-col">
      <div className="p-4 text-lg font-bold tracking-wide">HemaSuite</div>
      <div className="px-3 py-2 text-xs text-slate-400 uppercase">Phases</div>
      <nav className="flex-1 overflow-y-auto">
        {PHASES.map((phase, i) => (
          <button
            key={i}
            onClick={() => onPhaseSelect(i)}
            className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 ${
              activePhase === i
                ? "bg-slate-700 text-white"
                : "hover:bg-slate-800 text-slate-300"
            }`}
          >
            <span className="text-slate-500 text-xs w-4">{i + 1}</span>
            {phase}
          </button>
        ))}
      </nav>
      <div className="p-3 text-xs text-slate-500 border-t border-slate-700">
        v0.1.0
      </div>
    </aside>
  );
}

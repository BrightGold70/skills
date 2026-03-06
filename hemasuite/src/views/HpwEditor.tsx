import { useEffect, useState } from "react";
import { api } from "../hooks/useApi";
import { ManuscriptEditor } from "../components/ManuscriptEditor";

interface Phase {
  id: number;
  name: string;
  module: string;
}

export function HpwEditor() {
  const [phases, setPhases] = useState<Phase[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingPhase, setEditingPhase] = useState<Phase | null>(null);
  const [content, setContent] = useState("");

  useEffect(() => {
    api<Phase[]>("/hpw/phases")
      .then(setPhases)
      .catch((e) => setError(e.message));
  }, []);

  const openPhase = async (phase: Phase) => {
    try {
      const res = await api<{ content: string }>(`/hpw/manuscript/default/${phase.id}`);
      setContent(res.content);
      setEditingPhase(phase);
    } catch {
      setContent("");
      setEditingPhase(phase);
    }
  };

  const handleInsertResults = async () => {
    if (!editingPhase) return;
    try {
      const res = await api<{ content: string }>("/hpw/insert-results", {
        method: "POST",
        body: JSON.stringify({
          project_id: "default",
          phase_id: editingPhase.id,
          csa_output_dir: "/tmp/hemasuite-out",
          insert_mode: "append",
        }),
      });
      setContent(res.content);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Insert failed");
    }
  };

  if (error && phases.length === 0) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        Sidecar not available: {error}
      </div>
    );
  }

  if (editingPhase) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setEditingPhase(null)}
            className="text-sm text-blue-600 hover:underline"
          >
            Back to phases
          </button>
          <h2 className="text-xl font-semibold">
            Phase {editingPhase.id}: {editingPhase.name}
          </h2>
          <button
            onClick={handleInsertResults}
            className="ml-auto px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
          >
            Insert CSA Results
          </button>
        </div>
        <ManuscriptEditor content={content} onUpdate={setContent} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Manuscript Editor</h2>
      <div className="grid grid-cols-2 gap-4">
        {phases.map((p) => (
          <div
            key={p.id}
            onClick={() => openPhase(p)}
            className="p-4 bg-white rounded-lg border shadow-sm hover:border-blue-400 cursor-pointer transition-colors"
          >
            <span className="text-sm text-gray-400">Phase {p.id}</span>
            <h3 className="font-medium">{p.name}</h3>
          </div>
        ))}
      </div>
    </div>
  );
}

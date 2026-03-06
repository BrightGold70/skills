import { useEffect, useState } from "react";
import { api } from "../hooks/useApi";

interface Phase {
  id: number;
  name: string;
  module: string;
}

export function HpwEditor() {
  const [phases, setPhases] = useState<Phase[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Phase[]>("/hpw/phases")
      .then(setPhases)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        Sidecar not available: {error}
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

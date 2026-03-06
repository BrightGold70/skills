import { useState } from "react";
import { api } from "../hooks/useApi";

interface PipelineStep {
  step: string;
  status: "pending" | "running" | "done" | "error";
  output: string;
  duration_ms: number | null;
}

interface PipelineResult {
  steps: PipelineStep[];
}

const STEP_NAMES = ["Extract", "Validate", "Analyze", "Report"];

export function PipelineMonitor() {
  const [steps, setSteps] = useState<PipelineStep[]>(
    STEP_NAMES.map((name) => ({
      step: name.toLowerCase(),
      status: "pending",
      output: "",
      duration_ms: null,
    }))
  );
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataPath, setDataPath] = useState("");
  const [outputDir, setOutputDir] = useState("/tmp/hemasuite-out");

  const runPipeline = async () => {
    setRunning(true);
    setError(null);
    setSteps((prev) =>
      prev.map((s) => ({ ...s, status: "running" as const, output: "", duration_ms: null }))
    );

    try {
      const result = await api<PipelineResult>("/csa/pipeline", {
        method: "POST",
        body: JSON.stringify({ data_path: dataPath, output_dir: outputDir }),
      });
      setSteps(result.steps);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Pipeline failed");
    } finally {
      setRunning(false);
    }
  };

  const statusIcon = (status: PipelineStep["status"]) => {
    switch (status) {
      case "done": return "bg-green-500";
      case "running": return "bg-blue-500 animate-pulse";
      case "error": return "bg-red-500";
      default: return "bg-gray-300";
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">CRF Pipeline Monitor</h2>

      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <label className="block text-sm text-gray-600 mb-1">Data File</label>
          <input
            type="text"
            value={dataPath}
            onChange={(e) => setDataPath(e.target.value)}
            placeholder="/path/to/data.csv"
            className="w-full px-3 py-2 border rounded-lg text-sm"
          />
        </div>
        <div className="flex-1">
          <label className="block text-sm text-gray-600 mb-1">Output Dir</label>
          <input
            type="text"
            value={outputDir}
            onChange={(e) => setOutputDir(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          />
        </div>
        <button
          onClick={runPipeline}
          disabled={running}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm disabled:opacity-50 hover:bg-blue-700"
        >
          Run Pipeline
        </button>
      </div>

      <div className="space-y-2">
        {steps.map((s, i) => (
          <div key={s.step} className="flex items-center gap-3 p-3 bg-white rounded-lg border">
            <div className={`w-3 h-3 rounded-full ${statusIcon(s.status)}`} />
            <span className="font-medium w-20">{STEP_NAMES[i]}</span>
            <span className="text-sm text-gray-500 capitalize">{s.status}</span>
            {s.duration_ms !== null && (
              <span className="text-xs text-gray-400">{(s.duration_ms / 1000).toFixed(1)}s</span>
            )}
            {s.output && (
              <span className="text-xs text-gray-500 truncate flex-1">{s.output}</span>
            )}
          </div>
        ))}
      </div>

      {running && <div className="text-sm text-blue-600">Running pipeline...</div>}

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {steps.some((s) => s.output) && (
        <pre className="p-4 bg-gray-900 text-green-400 rounded-lg text-xs overflow-auto max-h-48">
          {steps.map((s) => s.output).filter(Boolean).join("\n")}
        </pre>
      )}
    </div>
  );
}

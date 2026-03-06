import { useEffect, useState } from "react";
import { api } from "../hooks/useApi";
import { ResultChart, tryParseChartData } from "../components/ResultChart";

interface Script {
  name: string;
  path: string;
}

interface RunResult {
  exit_code: number;
  stdout: string;
  stderr: string;
}

export function CsaDashboard() {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [running, setRunning] = useState<string | null>(null);
  const [result, setResult] = useState<RunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Script[]>("/csa/scripts")
      .then(setScripts)
      .catch((e) => setError(e.message));
  }, []);

  const runScript = async (name: string) => {
    setRunning(name);
    setResult(null);
    try {
      const res = await api<RunResult>("/csa/run", {
        method: "POST",
        body: JSON.stringify({ script: name, output_dir: "/tmp/hemasuite-out" }),
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setRunning(null);
    }
  };

  if (error && scripts.length === 0) {
    return (
      <div className="p-4 bg-amber-50 text-amber-700 rounded-lg">
        CSA not configured: {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Statistical Analysis</h2>
      <div className="grid grid-cols-3 gap-3">
        {scripts.map((s) => (
          <button
            key={s.name}
            onClick={() => runScript(s.name)}
            disabled={running !== null}
            className="p-3 bg-white rounded-lg border text-left hover:border-blue-400 disabled:opacity-50 transition-colors"
          >
            <span className="text-sm font-mono">{s.name}</span>
          </button>
        ))}
      </div>
      {running && (
        <div className="text-sm text-gray-500">Running {running}...</div>
      )}
      {result && (() => {
        const chartData = tryParseChartData(result.stdout);
        if (chartData) {
          return <ResultChart data={chartData} />;
        }
        return (
          <pre className="mt-4 p-4 bg-gray-900 text-green-400 rounded-lg text-xs overflow-auto max-h-64">
            {result.stdout || result.stderr}
          </pre>
        );
      })()}
    </div>
  );
}

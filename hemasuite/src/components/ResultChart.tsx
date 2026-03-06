import {
  ResponsiveContainer,
  LineChart,
  BarChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export interface ChartData {
  type: "km-curve" | "forest-plot" | "bar" | "line";
  title: string;
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
  series?: string[];
}

interface ResultChartProps {
  data: ChartData;
}

export function ResultChart({ data }: ResultChartProps) {
  const isLineType = data.type === "km-curve" || data.type === "line";

  return (
    <div className="bg-white rounded-lg border p-4">
      <h3 className="text-sm font-semibold mb-3">{data.title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        {isLineType ? (
          <LineChart data={data.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={data.xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type={data.type === "km-curve" ? "stepAfter" : "monotone"}
              dataKey={data.yKey}
              stroke="#2563eb"
              strokeWidth={2}
            />
            {data.series?.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={["#dc2626", "#16a34a", "#ca8a04"][i % 3]}
              />
            ))}
          </LineChart>
        ) : (
          <BarChart data={data.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={data.xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={data.yKey} fill="#2563eb" />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

export function tryParseChartData(stdout: string): ChartData | null {
  try {
    const parsed = JSON.parse(stdout);
    if (parsed.chart && parsed.chart.type && parsed.chart.data) {
      return parsed.chart as ChartData;
    }
    return null;
  } catch {
    return null;
  }
}

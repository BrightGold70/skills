import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultChart, type ChartData } from "./ResultChart";

// Mock recharts to avoid canvas/SVG rendering issues in jsdom
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ErrorBar: () => <div data-testid="error-bar" />,
}));

describe("ResultChart", () => {
  const kmData: ChartData = {
    type: "km-curve",
    title: "Overall Survival",
    data: [
      { time: 0, survival: 1.0 },
      { time: 6, survival: 0.85 },
      { time: 12, survival: 0.72 },
    ],
    xKey: "time",
    yKey: "survival",
  };

  const forestData: ChartData = {
    type: "forest-plot",
    title: "Hazard Ratios",
    data: [
      { study: "Study A", hr: 0.8, lower: 0.6, upper: 1.0 },
      { study: "Study B", hr: 1.2, lower: 0.9, upper: 1.5 },
    ],
    xKey: "study",
    yKey: "hr",
  };

  it("renders LineChart for km-curve type", () => {
    render(<ResultChart data={kmData} />);
    expect(screen.getByTestId("line-chart")).toBeTruthy();
    expect(screen.getByText("Overall Survival")).toBeTruthy();
  });

  it("renders BarChart for forest-plot type", () => {
    render(<ResultChart data={forestData} />);
    expect(screen.getByTestId("bar-chart")).toBeTruthy();
    expect(screen.getByText("Hazard Ratios")).toBeTruthy();
  });

  it("renders LineChart for line type", () => {
    const lineData: ChartData = {
      type: "line",
      title: "Trend",
      data: [{ x: 1, y: 10 }],
      xKey: "x",
      yKey: "y",
    };
    render(<ResultChart data={lineData} />);
    expect(screen.getByTestId("line-chart")).toBeTruthy();
  });

  it("renders BarChart for bar type", () => {
    const barData: ChartData = {
      type: "bar",
      title: "Distribution",
      data: [{ category: "A", count: 5 }],
      xKey: "category",
      yKey: "count",
    };
    render(<ResultChart data={barData} />);
    expect(screen.getByTestId("bar-chart")).toBeTruthy();
  });

  it("handles empty data gracefully", () => {
    const emptyData: ChartData = {
      type: "line",
      title: "Empty",
      data: [],
      xKey: "x",
      yKey: "y",
    };
    render(<ResultChart data={emptyData} />);
    expect(screen.getByText("Empty")).toBeTruthy();
  });
});

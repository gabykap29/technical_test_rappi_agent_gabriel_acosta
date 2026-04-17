"use client";

import { useContext } from "react";
import dynamic from "next/dynamic";
import { ThemeContext } from "@/features/agent/OperationsDashboard";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

type PlotlyChartProps = {
  data: Record<string, unknown>;
  title?: string;
};

export function PlotlyChart({ data, title }: PlotlyChartProps) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  const layout = data.layout as Record<string, unknown> || {};
  const chartData = data.data as unknown[] || [];

  const processedLayout = {
    ...layout,
    paper_bgcolor: isDark ? "#1f1f1f" : "#ffffff",
    plot_bgcolor: isDark ? "#1f1f1f" : "#ffffff",
    font: {
      color: isDark ? "#f3f4f6" : "#1f1f1f",
    },
    colorway: ["#ff3b30", "#ff7a1a", "#ffb15c", "#d82f19", "#ff5f3b", "#f59e0b"],
    title: title || layout.title,
  };

  return (
    <Plot
      data={chartData}
      layout={processedLayout}
      style={{ width: "100%", height: "350px" }}
      useResizeHandler={true}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
}

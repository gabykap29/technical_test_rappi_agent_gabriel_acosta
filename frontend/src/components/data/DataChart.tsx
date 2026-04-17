"use client";

import { useContext, useMemo, useState } from "react";
import {
  BarChart as RechartsBarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from "recharts";
import { ThemeContext } from "@/features/agent/OperationsDashboard";
import { BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon, ScatterChart as ScatterChartIcon } from "lucide-react";

type ChartData = {
  rows: Record<string, unknown>[];
  columns: string[];
  chartType?: "bar" | "line" | "scatter" | "pie" | "area";
};

const COLORS = ["#ff3b30", "#ff7a1a", "#ffb15c", "#d82f19", "#ff5f3b", "#f59e0b", "#b91c1c", "#fed7aa"];

export function DataChart({ rows, columns, chartType: defaultType = "bar" }: ChartData) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";
  const [chartType, setChartType] = useState(defaultType);

  const numericColumns = useMemo(
    () => columns.filter((col) => rows.some((row) => typeof row[col] === "number")),
    [columns, rows]
  );

  const labelColumn = useMemo(
    () => columns.find((col) => col.toUpperCase().includes("ZONE") || col.toUpperCase().includes("CITY") || col.toUpperCase().includes("COUNTRY")),
    [columns]
  );

  const data = useMemo(() => {
    if (!rows.length || !labelColumn || !numericColumns.length) return [];
    return rows.slice(0, 12).map((row) => {
      const obj: Record<string, string | number> = { name: String(row[labelColumn] ?? "") };
      numericColumns.forEach((col) => {
        obj[col] = Number(row[col]) || 0;
      });
      return obj;
    });
  }, [rows, labelColumn, numericColumns]);

  if (!data.length || !numericColumns.length) {
    return <p className="text-theme-muted text-sm">No chart data available.</p>;
  }

  const PrimaryYAxis = numericColumns[0];
  const SecondaryYAxis = numericColumns[1];

  const chartTypes = [
    { id: "bar", label: "Barras", icon: BarChart3 },
    { id: "line", label: "Línea", icon: LineChartIcon },
    { id: "area", label: "Área", icon: LineChartIcon },
    { id: "scatter", label: "Dispersión", icon: ScatterChartIcon },
    { id: "pie", label: "Pie", icon: PieChartIcon },
  ] as const;

  const renderChart = () => {
    const textColor = isDark ? "#f3f4f6" : "#1f1f1f";
    const gridColor = isDark ? "#343434" : "#e5e7eb";
    const tooltipBackground = isDark ? "#1f1f1f" : "#ffffff";

    switch (chartType) {
      case "line":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: textColor }} />
              <YAxis tick={{ fontSize: 10, fill: textColor }} />
              <Tooltip contentStyle={{ backgroundColor: tooltipBackground, borderColor: gridColor }} />
              <Legend />
              {numericColumns.map((col, idx) => (
                <Line key={col} type="monotone" dataKey={col} stroke={COLORS[idx % COLORS.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case "area":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: textColor }} />
              <YAxis tick={{ fontSize: 10, fill: textColor }} />
              <Tooltip contentStyle={{ backgroundColor: tooltipBackground, borderColor: gridColor }} />
              <Legend />
              {numericColumns.map((col, idx) => (
                <Area key={col} type="monotone" dataKey={col} stroke={COLORS[idx % COLORS.length]} fill={COLORS[idx % COLORS.length]} fillOpacity={0.3} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );

      case "scatter":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey={PrimaryYAxis} name={PrimaryYAxis} tick={{ fontSize: 10, fill: textColor }} />
              <YAxis dataKey={SecondaryYAxis || numericColumns[0]} name={SecondaryYAxis || numericColumns[0]} tick={{ fontSize: 10, fill: textColor }} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ backgroundColor: tooltipBackground, borderColor: gridColor }} />
              <Legend />
              <Scatter name={PrimaryYAxis} data={data} fill={COLORS[0]} />
              {SecondaryYAxis && <Scatter name={SecondaryYAxis} data={data} fill={COLORS[1]} />}
            </ScatterChart>
          </ResponsiveContainer>
        );

      case "pie":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                dataKey={PrimaryYAxis}
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={{ fontSize: 10, fill: textColor }}
              >
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: tooltipBackground, borderColor: gridColor }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return (
          <ResponsiveContainer width="100%" height={300}>
            <RechartsBarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: textColor }} />
              <YAxis tick={{ fontSize: 10, fill: textColor }} />
              <Tooltip contentStyle={{ backgroundColor: tooltipBackground, borderColor: gridColor }} />
              <Legend />
              {numericColumns.map((col, idx) => (
                <Bar key={col} dataKey={col} fill={COLORS[idx % COLORS.length]} />
              ))}
            </RechartsBarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1">
        {chartTypes.map((type) => {
          const Icon = type.icon;
          return (
            <button
              key={type.id}
              onClick={() => setChartType(type.id)}
              className={`flex items-center gap-1 px-2 py-1 text-xs rounded transition ${
                chartType === type.id
                  ? isDark
                    ? "bg-[#d82f19] text-white"
                    : "bg-[#ff4f2e] text-white"
                  : isDark
                    ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                    : "bg-[var(--accent-soft)] text-[#9a3412] hover:bg-[#ffe0cf]"
              }`}
            >
              <Icon size={12} />
              {type.label}
            </button>
          );
        })}
      </div>
      {renderChart()}
    </div>
  );
}

import { useContext } from "react";
import { ThemeContext } from "@/features/agent/OperationsDashboard";

type MiniBarChartProps = {
  rows: Record<string, unknown>[];
  columns: string[];
};

export function MiniBarChart({ rows, columns }: MiniBarChartProps) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  const labelColumn = columns.find((column) => column.toUpperCase().includes("ZONE"));
  const valueColumn = [...columns]
    .reverse()
    .find((column) => rows.some((row) => typeof row[column] === "number"));

  if (!labelColumn || !valueColumn || rows.length === 0) {
    return <p className="text-theme-muted text-sm">No chart available for this answer.</p>;
  }

  const chartRows = rows.slice(0, 8).map((row) => ({
    label: String(row[labelColumn] ?? ""),
    value: Number(row[valueColumn] ?? 0),
  }));
  const maxValue = Math.max(...chartRows.map((row) => Math.abs(row.value)), 1);

  return (
    <div className="space-y-3">
      <p className="text-theme text-sm font-semibold">{valueColumn} by {labelColumn}</p>
      {chartRows.map((row) => (
        <div className="grid grid-cols-[160px_1fr_90px] items-center gap-3" key={row.label}>
          <span className="text-theme-muted truncate text-sm" title={row.label}>
            {row.label}
          </span>
          <div className={`h-3 rounded-full ${isDark ? 'bg-gray-700' : 'bg-[#e4ece7]'}`}>
            <div
              className="h-3 rounded-full bg-[#16834f]"
              style={{ width: `${Math.max((Math.abs(row.value) / maxValue) * 100, 3)}%` }}
            />
          </div>
          <span className="text-theme text-right text-sm font-semibold">
            {Number.isInteger(row.value) ? row.value : row.value.toFixed(3)}
          </span>
        </div>
      ))}
    </div>
  );
}

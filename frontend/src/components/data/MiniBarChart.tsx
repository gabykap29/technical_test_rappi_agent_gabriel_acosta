type MiniBarChartProps = {
  rows: Record<string, unknown>[];
  columns: string[];
};

export function MiniBarChart({ rows, columns }: MiniBarChartProps) {
  const labelColumn = columns.find((column) => column.toUpperCase().includes("ZONE"));
  const valueColumn = [...columns]
    .reverse()
    .find((column) => rows.some((row) => typeof row[column] === "number"));

  if (!labelColumn || !valueColumn || rows.length === 0) {
    return <p className="text-sm text-[#66746d]">No chart available for this answer.</p>;
  }

  const chartRows = rows.slice(0, 8).map((row) => ({
    label: String(row[labelColumn] ?? ""),
    value: Number(row[valueColumn] ?? 0),
  }));
  const maxValue = Math.max(...chartRows.map((row) => Math.abs(row.value)), 1);

  return (
    <div className="space-y-3">
      <p className="text-sm font-semibold text-[#29342f]">{valueColumn} by {labelColumn}</p>
      {chartRows.map((row) => (
        <div className="grid grid-cols-[160px_1fr_90px] items-center gap-3" key={row.label}>
          <span className="truncate text-sm text-[#4d5d55]" title={row.label}>
            {row.label}
          </span>
          <div className="h-3 rounded-full bg-[#e4ece7]">
            <div
              className="h-3 rounded-full bg-[#16834f]"
              style={{ width: `${Math.max((Math.abs(row.value) / maxValue) * 100, 3)}%` }}
            />
          </div>
          <span className="text-right text-sm font-semibold">
            {Number.isInteger(row.value) ? row.value : row.value.toFixed(3)}
          </span>
        </div>
      ))}
    </div>
  );
}

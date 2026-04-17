import { useContext } from "react";
import { ThemeContext } from "@/features/agent/OperationsDashboard";

type EvidenceTableProps = {
  columns: string[];
  rows: Record<string, unknown>[];
  query?: string;
};

export function EvidenceTable({ columns, rows, query }: EvidenceTableProps) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  if (!rows.length) {
    return <p className="text-theme-muted text-sm">No evidence table returned.</p>;
  }

  return (
    <div>
      {query && (
        <div className={`mb-2 px-2 py-1 rounded text-xs font-mono ${isDark ? 'bg-gray-800 text-gray-400' : 'bg-[#f5f5f5] text-[#666]'}`}>
          Query: {query}
        </div>
      )}
      <div className={`max-h-[420px] overflow-auto rounded-lg border ${isDark ? 'border-gray-700' : 'border-[#d9e4dd]'}`}>
        <table className="text-theme w-full min-w-[680px] border-collapse text-left text-sm">
          <thead className={`sticky top-0 ${isDark ? 'bg-gray-800' : 'bg-[#f1f6f3]'}`}>
            <tr>
              {columns.map((column) => (
                <th className={`border-b px-3 py-2 ${isDark ? 'border-gray-700' : 'border-[#d9e4dd]'}`} key={column}>
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr className={rowIndex % 2 === 0 
                ? (isDark ? 'bg-gray-900' : 'bg-white')
                : (isDark ? 'bg-gray-800' : 'bg-[#fbfdfc]')
              } key={rowIndex}>
                {columns.map((column) => (
                  <td className={`border-b px-3 py-2 ${isDark ? 'border-gray-700' : 'border-[#eef3f0]'}`} key={column}>
                    {formatValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatValue(value: unknown): string {
  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toString() : value.toFixed(4);
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

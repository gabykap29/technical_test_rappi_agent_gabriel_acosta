import { useContext, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { ThemeContext } from "@/features/agent/OperationsDashboard";

type EvidenceTableProps = {
  columns: string[];
  rows: Record<string, unknown>[];
  query?: string;
};

export function EvidenceTable({ columns, rows, query }: EvidenceTableProps) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";
  const [showQuery, setShowQuery] = useState(false);

  if (!rows.length) {
    return <p className="text-theme-muted text-sm">No evidence table returned.</p>;
  }

  return (
    <div>
      {query && (
        <button
          type="button"
          onClick={() => setShowQuery(!showQuery)}
          className={`mb-2 flex items-center gap-1 text-xs font-medium ${
            isDark ? "text-blue-400" : "text-blue-600"
          }`}
        >
          {showQuery ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          Ver consulta
        </button>
      )}
      {showQuery && query && (
        <pre className={`mb-2 p-2 rounded text-xs font-mono overflow-x-auto ${
          isDark ? "bg-gray-800 text-gray-300" : "bg-[#f5f5f5] text-[#444]"
        }`}>
          {query}
        </pre>
      )}
      <div className={`max-h-[420px] overflow-auto rounded-lg border ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
        <table className="text-theme w-full min-w-[680px] border-collapse text-left text-sm">
          <thead className={`sticky top-0 ${isDark ? 'bg-gray-800' : 'bg-gray-100'}`}>
            <tr>
              {columns.map((column) => (
                <th className={`border-b px-3 py-2 ${isDark ? 'border-gray-700' : 'border-gray-200'}`} key={column}>
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr className={rowIndex % 2 === 0 
                ? (isDark ? 'bg-gray-900' : 'bg-white')
                : (isDark ? 'bg-gray-800' : 'bg-gray-50')
              } key={rowIndex}>
                {columns.map((column) => (
                  <td className={`border-b px-3 py-2 ${isDark ? 'border-gray-700' : 'border-gray-100'}`} key={column}>
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

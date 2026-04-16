type EvidenceTableProps = {
  columns: string[];
  rows: Record<string, unknown>[];
};

export function EvidenceTable({ columns, rows }: EvidenceTableProps) {
  if (!rows.length) {
    return <p className="text-sm text-[#66746d]">No evidence table returned.</p>;
  }

  return (
    <div className="max-h-[420px] overflow-auto rounded-lg border border-[#d9e4dd]">
      <table className="w-full min-w-[680px] border-collapse text-left text-sm">
        <thead className="sticky top-0 bg-[#f1f6f3]">
          <tr>
            {columns.map((column) => (
              <th className="border-b border-[#d9e4dd] px-3 py-2" key={column}>
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr className="odd:bg-white even:bg-[#fbfdfc]" key={rowIndex}>
              {columns.map((column) => (
                <td className="border-b border-[#eef3f0] px-3 py-2" key={column}>
                  {formatValue(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
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

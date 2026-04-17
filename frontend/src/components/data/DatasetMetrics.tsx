import { useContext } from "react";
import { ThemeContext } from "@/features/agent/OperationsDashboard";
import type { DatasetOverview } from "@/types/api";

type DatasetMetricsProps = {
  overview: DatasetOverview | null;
  loading: boolean;
};

const metricLabels: Array<[keyof DatasetOverview, string]> = [
  ["countries", "Countries"],
  ["zones", "Zones"],
  ["metrics", "Metrics"],
  ["analyticalRows", "Analytical rows"],
];

export function DatasetMetrics({ overview, loading }: DatasetMetricsProps) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  return (
    <section className="mb-4 grid gap-3 md:grid-cols-4">
      {metricLabels.map(([key, label]) => (
        <article className={`panel p-4 ${isDark ? 'bg-gray-900 border-gray-700' : ''}`} key={key}>
          <p className="text-theme-muted text-sm">{label}</p>
          <p className="text-theme mt-2 text-2xl font-bold">
            {loading || !overview ? "..." : overview[key].toLocaleString()}
          </p>
        </article>
      ))}
    </section>
  );
}

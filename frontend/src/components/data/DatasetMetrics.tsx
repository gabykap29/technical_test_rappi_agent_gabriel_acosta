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
  return (
    <section className="mb-4 grid gap-3 md:grid-cols-4">
      {metricLabels.map(([key, label]) => (
        <article className="panel p-4" key={key}>
          <p className="text-sm text-[#66746d]">{label}</p>
          <p className="mt-2 text-2xl font-bold text-[#1d2421]">
            {loading || !overview ? "..." : overview[key].toLocaleString()}
          </p>
        </article>
      ))}
    </section>
  );
}

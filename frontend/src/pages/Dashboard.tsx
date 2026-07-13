import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { BarList, ColumnChart, Donut, HeatMap, StatTile } from "../components/charts";

interface DashboardData {
  total_profiles: number;
  active_profiles: number;
  by_status: Record<string, number>;
  by_grade: Record<string, number>;
  by_division: { name: string; count: number }[];
  by_job_family: { name: string; count: number }[];
  competency_distribution: Record<string, number>;
  top_competencies: { name: string; count: number }[];
  outdated_profiles: number;
  awaiting_approval: number;
  avg_review_age_days: number | null;
  career_path_coverage: number;
  profiles_missing_grade: number;
}
interface HeatData { grades: string[]; rows: Record<string, number | string>[] }

const GRADE_ORDER = ["1", "2", "2H", "3", "3H", "4", "5"];

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [heat, setHeat] = useState<HeatData | null>(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api<DashboardData>("/api/analytics/dashboard").then(setData).catch((e) => setError(e.message));
    api<HeatData>("/api/analytics/heatmap").then(setHeat).catch(() => {});
  }, []);

  if (error) return <div className="card p-6 text-status-critical">Failed to load dashboard: {error}</div>;
  if (!data) return <div className="p-6 text-ink-muted">Loading analytics…</div>;

  const reviewYears = data.avg_review_age_days ? (data.avg_review_age_days / 365).toFixed(1) : "—";
  const statusData = Object.entries(data.by_status)
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => ({ name, count }));

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-bold">Executive Dashboard</h1>
          <p className="text-sm text-ink-muted">Organization-wide job architecture health</p>
        </div>
        <button className="btn-brand" onClick={() => navigate("/profiles")}>Browse repository →</button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <StatTile label="Total job profiles" value={data.total_profiles.toLocaleString()} hint={`${data.active_profiles.toLocaleString()} active`} />
        <StatTile label="Awaiting approval" value={data.awaiting_approval} tone={data.awaiting_approval > 0 ? "warning" : "good"} hint="In review workflow" />
        <StatTile label="Outdated (>2y)" value={data.outdated_profiles.toLocaleString()} tone={data.outdated_profiles > 0 ? "critical" : "good"} hint={`Avg review age ${reviewYears} yrs`} />
        <StatTile label="Career-path coverage" value={`${data.career_path_coverage}%`} hint="Profiles with a next role" />
        <StatTile label="Missing grade" value={data.profiles_missing_grade} tone={data.profiles_missing_grade > 0 ? "warning" : "good"} hint="Need level assignment" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card p-4 lg:col-span-1">
          <h2 className="mb-3 text-sm font-bold">Profiles by grade (Irancell levels)</h2>
          <ColumnChart data={data.by_grade} order={GRADE_ORDER} />
        </div>
        <div className="card p-4 lg:col-span-2">
          <h2 className="mb-3 text-sm font-bold">Profiles by division</h2>
          <BarList data={data.by_division} maxRows={10} onClick={(name) => navigate(`/profiles?division=${encodeURIComponent(name)}`)} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card p-4">
          <h2 className="mb-3 text-sm font-bold">Workflow status</h2>
          <Donut data={statusData.slice(0, 5)} />
        </div>
        <div className="card p-4 lg:col-span-2">
          <h2 className="mb-3 text-sm font-bold">Top technical competencies across profiles</h2>
          <BarList data={data.top_competencies} color="#1baf7a" maxRows={10} />
        </div>
      </div>

      {heat && (
        <div className="card p-4">
          <h2 className="mb-1 text-sm font-bold">Job family × grade heat map</h2>
          <p className="mb-3 text-xs text-ink-muted">Top 25 job families by profile count — darker cells mean more profiles at that level.</p>
          <HeatMap grades={heat.grades} rows={heat.rows} />
        </div>
      )}

      <div className="card p-4">
        <h2 className="mb-3 text-sm font-bold">Largest job families</h2>
        <BarList data={data.by_job_family} color="#4a3aa7" maxRows={12} onClick={(name) => navigate(`/profiles?job_family=${encodeURIComponent(name)}`)} />
      </div>
    </div>
  );
}

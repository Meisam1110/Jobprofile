import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Paged, ProfileSummary, STATUS_COLORS, Taxonomy, api, currentUser } from "../api";

export default function Repository() {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState<Paged<ProfileSummary> | null>(null);
  const [taxonomy, setTaxonomy] = useState<Taxonomy | null>(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const user = currentUser();
  const canEdit = user && ["hr", "admin"].includes(user.role);

  const page = Number(params.get("page") ?? 1);
  const filters = {
    q: params.get("q") ?? "",
    status: params.get("status") ?? "",
    grade: params.get("grade") ?? "",
    division: params.get("division") ?? "",
    job_family: params.get("job_family") ?? "",
  };

  useEffect(() => {
    api<Taxonomy>("/api/taxonomy").then(setTaxonomy).catch(() => {});
  }, []);

  useEffect(() => {
    const qs = new URLSearchParams({ page: String(page), page_size: "25" });
    Object.entries(filters).forEach(([k, v]) => v && qs.set(k, v));
    api<Paged<ProfileSummary>>(`/api/profiles?${qs}`).then(setData).catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.set("page", "1");
    setParams(next);
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Job Profile Repository</h1>
          <p className="text-sm text-ink-muted">{data ? `${data.total.toLocaleString()} profiles` : "Loading…"}</p>
        </div>
        {canEdit && (
          <Link to="/profiles/new" className="btn-brand">+ New job profile</Link>
        )}
      </div>

      <div className="card flex flex-wrap items-center gap-2 p-3">
        <input
          className="input max-w-64"
          placeholder="Filter by keyword…"
          defaultValue={filters.q}
          onKeyDown={(e) => e.key === "Enter" && setFilter("q", (e.target as HTMLInputElement).value)}
        />
        <select className="input max-w-44" value={filters.division} onChange={(e) => setFilter("division", e.target.value)}>
          <option value="">All divisions</option>
          {taxonomy?.divisions.map((d) => <option key={d.id} value={d.name}>{d.name}</option>)}
        </select>
        <select className="input max-w-32" value={filters.grade} onChange={(e) => setFilter("grade", e.target.value)}>
          <option value="">All levels</option>
          {taxonomy?.grades.map((g) => <option key={g.id} value={g.code}>Level {g.code}</option>)}
        </select>
        <select className="input max-w-44" value={filters.status} onChange={(e) => setFilter("status", e.target.value)}>
          <option value="">All statuses</option>
          {taxonomy?.statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        {(filters.q || filters.status || filters.grade || filters.division || filters.job_family) && (
          <button className="btn-ghost" onClick={() => setParams(new URLSearchParams())}>Clear filters</button>
        )}
      </div>

      {error && <div className="card p-4 text-status-critical">{error}</div>}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-plane text-left text-xs uppercase tracking-wide text-ink-muted">
            <tr>
              <th className="px-4 py-2.5">Job title</th>
              <th className="px-3 py-2.5">Division</th>
              <th className="px-3 py-2.5">Level</th>
              <th className="px-3 py-2.5">Reports to</th>
              <th className="px-3 py-2.5">Status</th>
              <th className="px-3 py-2.5 text-right">v</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((p) => (
              <tr
                key={p.id}
                className="cursor-pointer border-t border-black/5 hover:bg-plane"
                onClick={() => navigate(`/profiles/${p.id}`)}
              >
                <td className="px-4 py-2.5">
                  <div className="font-medium">{p.job_title}</div>
                  <div className="text-xs text-ink-muted">{p.job_code} · {p.location || "—"}</div>
                </td>
                <td className="px-3 py-2.5 text-ink-secondary">{p.division?.name ?? "—"}</td>
                <td className="px-3 py-2.5">
                  {p.grade ? (
                    <span className="rounded bg-plane px-1.5 py-0.5 text-xs font-semibold">{p.grade.code}</span>
                  ) : "—"}
                </td>
                <td className="max-w-52 truncate px-3 py-2.5 text-ink-secondary">{p.reports_to || "—"}</td>
                <td className="px-3 py-2.5">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[p.status] ?? "bg-gray-100"}`}>
                    {p.status}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums text-ink-muted">{p.version}</td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-ink-muted">No profiles match these filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {data && totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <button className="btn-ghost" disabled={page <= 1} onClick={() => setFilter("page", String(page - 1))}>← Previous</button>
          <span className="text-ink-muted">Page {page} of {totalPages}</span>
          <button className="btn-ghost" disabled={page >= totalPages} onClick={() => setFilter("page", String(page + 1))}>Next →</button>
        </div>
      )}
    </div>
  );
}

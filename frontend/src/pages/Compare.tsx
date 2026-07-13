import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";

interface CompareResult {
  a: { id: number; job_title: string };
  b: { id: number; job_title: string };
  fields: Record<string, { a: unknown; b: unknown; different: boolean }>;
  competencies: { only_a: string[]; only_b: string[]; shared: { name: string; a_level: string; b_level: string; different: boolean }[] };
  responsibilities: { a: string[]; b: string[] };
  kpis: { a: string[]; b: string[] };
  qualifications: { a: { type: string; text: string }[]; b: { type: string; text: string }[] };
}

const FIELD_LABELS: Record<string, string> = {
  job_title: "Job title", grade: "Level / Grade", location: "Location", reports_to: "Reports to",
  direct_reports: "Subordinates", mission: "Mission", context: "Context", authorities_text: "Authorities",
  education_text: "Education", experience_text: "Experience", trainings_text: "Trainings",
  working_conditions: "Working conditions", performance_standards: "Performance standards", status: "Status",
};

function ProfilePicker({ label, value, onChange }: { label: string; value: string; onChange: (id: string) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<{ id: number; job_title: string }[]>([]);
  const [selected, setSelected] = useState("");
  useEffect(() => {
    if (q.length < 2) return setHits([]);
    const t = setTimeout(() => {
      api<{ id: number; job_title: string }[]>(`/api/search/autocomplete?q=${encodeURIComponent(q)}`).then(setHits).catch(() => {});
    }, 200);
    return () => clearTimeout(t);
  }, [q]);
  useEffect(() => {
    if (value && !selected) {
      api<{ job_title: string }>(`/api/profiles/${value}`).then((p) => setSelected(p.job_title)).catch(() => {});
    }
  }, [value, selected]);
  return (
    <div className="relative flex-1">
      <label className="label">{label}</label>
      <input
        className="input"
        placeholder="Search a job profile…"
        value={q || selected}
        onChange={(e) => { setQ(e.target.value); setSelected(""); }}
      />
      {hits.length > 0 && (
        <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-black/10 bg-white shadow-lg">
          {hits.map((h) => (
            <button
              key={h.id}
              type="button"
              className="block w-full px-3 py-2 text-left text-sm hover:bg-plane"
              onClick={() => { onChange(String(h.id)); setSelected(h.job_title); setQ(""); setHits([]); }}
            >
              {h.job_title}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Compare() {
  const [params, setParams] = useSearchParams();
  const a = params.get("a") ?? "";
  const b = params.get("b") ?? "";
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState("");
  const [showSame, setShowSame] = useState(false);

  useEffect(() => {
    if (a && b) {
      api<CompareResult>(`/api/compare?a=${a}&b=${b}`).then((r) => { setResult(r); setError(""); }).catch((e) => setError(e.message));
    } else {
      setResult(null);
    }
  }, [a, b]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Comparison Engine</h1>
        <p className="text-sm text-ink-muted">Put two job profiles side by side — differences are highlighted.</p>
      </div>
      <div className="card flex flex-wrap gap-4 p-4">
        <ProfilePicker label="Profile A" value={a} onChange={(id) => setParams((p) => { p.set("a", id); return p; })} />
        <ProfilePicker label="Profile B" value={b} onChange={(id) => setParams((p) => { p.set("b", id); return p; })} />
        <label className="mt-5 flex items-center gap-2 text-sm text-ink-secondary">
          <input type="checkbox" checked={showSame} onChange={(e) => setShowSame(e.target.checked)} />
          Show identical fields
        </label>
      </div>
      {error && <div className="card p-4 text-status-critical">{error}</div>}
      {result && (
        <>
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-plane text-left text-xs uppercase text-ink-muted">
                <tr>
                  <th className="w-40 px-4 py-2">Field</th>
                  <th className="px-4 py-2"><Link className="hover:underline" to={`/profiles/${result.a.id}`}>{result.a.job_title}</Link></th>
                  <th className="px-4 py-2"><Link className="hover:underline" to={`/profiles/${result.b.id}`}>{result.b.job_title}</Link></th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.fields)
                  .filter(([, v]) => showSame || v.different)
                  .map(([field, v]) => (
                    <tr key={field} className={`border-t border-black/5 align-top ${v.different ? "bg-amber-50/60" : ""}`}>
                      <td className="px-4 py-2 font-medium">
                        {FIELD_LABELS[field] ?? field}
                        {v.different && <span className="ml-1 text-xs text-amber-700">≠</span>}
                      </td>
                      <td className="whitespace-pre-wrap px-4 py-2 text-ink-secondary">{String(v.a ?? "—").slice(0, 600) || "—"}</td>
                      <td className="whitespace-pre-wrap px-4 py-2 text-ink-secondary">{String(v.b ?? "—").slice(0, 600) || "—"}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <CompetencyList title={`Only in ${result.a.job_title}`} items={result.competencies.only_a} tone="a" />
            <div className="card p-4">
              <h3 className="mb-2 text-sm font-bold">Shared competencies ({result.competencies.shared.length})</h3>
              <ul className="max-h-72 space-y-1 overflow-auto text-sm">
                {result.competencies.shared.map((c) => (
                  <li key={c.name} className={`flex justify-between gap-2 rounded px-2 py-1 ${c.different ? "bg-amber-50" : ""}`}>
                    <span>{c.name}</span>
                    <span className="whitespace-nowrap text-xs text-ink-muted">{c.a_level} / {c.b_level}</span>
                  </li>
                ))}
              </ul>
            </div>
            <CompetencyList title={`Only in ${result.b.job_title}`} items={result.competencies.only_b} tone="b" />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="card p-4">
              <h3 className="mb-2 text-sm font-bold">Responsibilities — {result.a.job_title} ({result.responsibilities.a.length})</h3>
              <ul className="max-h-80 list-disc space-y-1 overflow-auto pl-4 text-sm text-ink-secondary">
                {result.responsibilities.a.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
            <div className="card p-4">
              <h3 className="mb-2 text-sm font-bold">Responsibilities — {result.b.job_title} ({result.responsibilities.b.length})</h3>
              <ul className="max-h-80 list-disc space-y-1 overflow-auto pl-4 text-sm text-ink-secondary">
                {result.responsibilities.b.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          </div>
        </>
      )}
      {!result && !error && <div className="card p-8 text-center text-sm text-ink-muted">Select two profiles to compare.</div>}
    </div>
  );
}

function CompetencyList({ title, items, tone }: { title: string; items: string[]; tone: "a" | "b" }) {
  return (
    <div className="card p-4">
      <h3 className="mb-2 text-sm font-bold">{title} ({items.length})</h3>
      <ul className="max-h-72 space-y-1 overflow-auto text-sm">
        {items.map((c) => (
          <li key={c} className={`rounded px-2 py-1 ${tone === "a" ? "bg-blue-50" : "bg-emerald-50"}`}>{c}</li>
        ))}
        {items.length === 0 && <li className="text-ink-muted">None</li>}
      </ul>
    </div>
  );
}

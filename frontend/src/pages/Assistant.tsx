import { useEffect, useState } from "react";
import { api } from "../api";

const TASKS: { id: string; label: string; needs: "title" | "text" | "question"; blurb: string }[] = [
  { id: "generate_profile", label: "Generate job profile", needs: "title", blurb: "Draft a complete profile from a job title, grounded in the Irancell corpus" },
  { id: "convert_jd", label: "Convert existing JD", needs: "text", blurb: "Paste any job description; get it restructured into the Irancell template" },
  { id: "recommend_competencies", label: "Recommend competencies", needs: "title", blurb: "Technical + behavioral competencies mined from similar roles" },
  { id: "recommend_kpis", label: "Recommend KPIs", needs: "title", blurb: "KPI set with types, weights and measurement methods" },
  { id: "recommend_responsibilities", label: "Recommend responsibilities", needs: "title", blurb: "Responsibility statements used by similar Irancell roles" },
  { id: "recommend_qualifications", label: "Recommend qualifications", needs: "title", blurb: "Education / experience / certifications for the role" },
  { id: "estimate_grade", label: "Estimate grade", needs: "title", blurb: "Level 1–5 estimate with evidence from graded profiles" },
  { id: "improve_writing", label: "Improve writing", needs: "text", blurb: "Rewrite profile text in clear professional HR language" },
  { id: "translate", label: "Translate", needs: "text", blurb: "Translate profile content (default: Persian)" },
  { id: "find_similar", label: "Find similar profiles", needs: "title", blurb: "Semantic search over the whole repository" },
];

export default function Assistant() {
  const [task, setTask] = useState(TASKS[0]);
  const [input, setInput] = useState("");
  const [result, setResult] = useState<{ provider: string; result: unknown } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [providerConfigured, setProviderConfigured] = useState(true);

  useEffect(() => {
    api<{ generative_provider_configured: boolean }>("/api/ai/tasks")
      .then((r) => setProviderConfigured(r.generative_provider_configured))
      .catch(() => {});
  }, []);

  async function run() {
    if (!input.trim()) return;
    setBusy(true);
    setError("");
    setResult(null);
    const body: Record<string, string> = { task: task.id };
    if (task.needs === "title") body.job_title = input.trim();
    else body.text = input.trim();
    try {
      setResult(await api("/api/ai", { method: "POST", body: JSON.stringify(body) }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">AI Assistant</h1>
        <p className="text-sm text-ink-muted">
          Grounded in the {providerConfigured ? "Claude API and the" : ""} imported Irancell profile corpus.
          {!providerConfigured && " Generative drafting is in corpus-mining mode — set JPMS_ANTHROPIC_API_KEY on the backend for full generation, rewriting and translation."}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-1.5">
          {TASKS.map((t) => (
            <button
              key={t.id}
              className={`block w-full rounded-xl border p-3 text-left text-sm transition-colors ${
                task.id === t.id ? "border-brand-ink bg-white shadow-sm" : "border-black/10 bg-white/60 hover:bg-white"
              }`}
              onClick={() => { setTask(t); setResult(null); }}
            >
              <div className="font-semibold">{t.label}</div>
              <div className="text-xs text-ink-muted">{t.blurb}</div>
            </button>
          ))}
        </div>

        <div className="lg:col-span-2">
          <div className="card p-4">
            <label className="label">
              {task.needs === "title" ? "Job title" : "Paste text"}
            </label>
            {task.needs === "title" ? (
              <input
                className="input"
                placeholder="e.g. Core Network Planning Senior Specialist"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && run()}
              />
            ) : (
              <textarea
                className="input"
                rows={8}
                placeholder="Paste the job description or profile text here…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
            )}
            <button className="btn-brand mt-3" disabled={busy || !input.trim()} onClick={run}>
              {busy ? "Working…" : `Run: ${task.label}`}
            </button>
            {error && <div className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-status-critical">{error}</div>}
          </div>

          {result && (
            <div className="card mt-4 p-4">
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-sm font-bold">Result</h2>
                <span className="rounded bg-plane px-2 py-0.5 text-xs text-ink-muted">provider: {result.provider}</span>
              </div>
              <ResultView value={result.result} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultView({ value }: { value: unknown }) {
  if (typeof value === "string") return <div className="whitespace-pre-wrap text-sm leading-relaxed">{value}</div>;
  if (Array.isArray(value)) {
    return (
      <ul className="space-y-1 text-sm">
        {value.map((item, i) => (
          <li key={i} className="rounded-lg bg-plane px-3 py-1.5">
            {typeof item === "string" ? item : <ObjectRow obj={item as Record<string, unknown>} />}
          </li>
        ))}
      </ul>
    );
  }
  if (value && typeof value === "object") {
    return (
      <dl className="space-y-2 text-sm">
        {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{k.replaceAll("_", " ")}</dt>
            <dd className="mt-0.5"><ResultView value={v} /></dd>
          </div>
        ))}
      </dl>
    );
  }
  return <span className="text-sm">{String(value)}</span>;
}

function ObjectRow({ obj }: { obj: Record<string, unknown> }) {
  const name = obj.name ?? obj.title ?? obj.job_title ?? obj.text;
  const rest = Object.entries(obj).filter(([k]) => !["name", "title", "job_title", "text"].includes(k));
  return (
    <span>
      <span className="font-medium">{String(name ?? "")}</span>
      {rest.length > 0 && (
        <span className="ml-2 text-xs text-ink-muted">
          {rest.map(([k, v]) => `${k}: ${String(v)}`).join(" · ")}
        </span>
      )}
    </span>
  );
}

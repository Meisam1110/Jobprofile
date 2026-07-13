import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  CareerEdge, ProfileDetail as Detail, STATUS_COLORS, User, Version, WorkflowEvent, api, exportUrl,
} from "../api";

const TABS = ["Overview", "Responsibilities", "Competencies", "Qualifications", "Career Path", "Workflow", "AI Assistant"] as const;
type Tab = (typeof TABS)[number];

export default function ProfileDetail({ user }: { user: User }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<Detail | null>(null);
  const [tab, setTab] = useState<Tab>("Overview");
  const [error, setError] = useState("");

  const reload = useCallback(() => {
    api<Detail>(`/api/profiles/${id}`).then(setProfile).catch((e) => setError(e.message));
  }, [id]);
  useEffect(reload, [reload]);

  if (error) return <div className="card p-6 text-status-critical">{error}</div>;
  if (!profile) return <div className="p-6 text-ink-muted">Loading profile…</div>;

  const canEdit = ["hr", "admin"].includes(user.role);

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">{profile.job_title}</h1>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[profile.status] ?? "bg-gray-100"}`}>
                {profile.status}
              </span>
            </div>
            <div className="mt-1 text-sm text-ink-muted">
              {profile.job_code} · {profile.division?.name ?? "—"} · {profile.location || "—"} · Document v{profile.document_version} (rev {profile.version})
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <a className="btn-ghost" href={exportUrl(profile.id, "pdf")}>PDF</a>
            <a className="btn-ghost" href={exportUrl(profile.id, "docx")}>Word</a>
            <a className="btn-ghost" href={exportUrl(profile.id, "json")}>JSON</a>
            <button className="btn-ghost" onClick={() => navigate(`/compare?a=${profile.id}`)}>Compare</button>
            {canEdit && (
              <>
                <button
                  className="btn-ghost"
                  onClick={() => api(`/api/profiles/${profile.id}/duplicate`, { method: "POST" }).then((p) => navigate(`/profiles/${(p as Detail).id}/edit`))}
                >
                  Use as template
                </button>
                <Link className="btn-primary" to={`/profiles/${profile.id}/edit`}>Edit</Link>
              </>
            )}
          </div>
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 text-sm md:grid-cols-4">
          <Meta label="Level / Grade" value={profile.grade ? `${profile.grade.code} — ${profile.grade.band}` : profile.org_level || "—"} />
          <Meta label="Reports to" value={profile.reports_to || "—"} />
          <Meta label="Subordinates" value={String(profile.direct_reports)} />
          <Meta label="Employment" value={profile.employment_type || "—"} />
          <Meta label="Role family" value={profile.role_family?.name ?? "—"} />
          <Meta label="Job family" value={profile.job_family?.name ?? "—"} />
          <Meta label="Department" value={profile.department?.name ?? "—"} />
          <Meta label="Approved" value={profile.approved_date ? new Date(profile.approved_date).toLocaleDateString() : "—"} />
        </dl>
      </div>

      <div className="card">
        <div className="flex overflow-x-auto border-b border-black/10 px-2">
          {TABS.map((t) => (
            <button key={t} className={`tab ${tab === t ? "tab-active" : ""}`} onClick={() => setTab(t)}>{t}</button>
          ))}
        </div>
        <div className="p-5">
          {tab === "Overview" && <Overview profile={profile} />}
          {tab === "Responsibilities" && <Responsibilities profile={profile} />}
          {tab === "Competencies" && <Competencies profile={profile} />}
          {tab === "Qualifications" && <Qualifications profile={profile} />}
          {tab === "Career Path" && <CareerPath profile={profile} />}
          {tab === "Workflow" && <Workflow profile={profile} user={user} onChange={reload} />}
          {tab === "AI Assistant" && <AIPanel profile={profile} />}
        </div>
      </div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{label}</dt>
      <dd className="text-ink">{value}</dd>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-5">
      <h3 className="mb-1.5 border-l-4 border-brand pl-2 text-sm font-bold">{title}</h3>
      <div className="whitespace-pre-wrap text-sm leading-relaxed text-ink-secondary">{children}</div>
    </section>
  );
}

function Overview({ profile }: { profile: Detail }) {
  const collab = profile.collaboration ?? {};
  return (
    <div>
      <Section title="Mission">{profile.mission || "—"}</Section>
      <Section title="Context">{profile.context || "—"}</Section>
      <Section title="Collaboration">
        <dl className="grid gap-2 md:grid-cols-2">
          {[
            ["Direct reports", collab.direct_reports],
            ["Matrix reports to", collab.matrix_reports],
            ["Key customers", collab.key_customers],
            ["Key suppliers", collab.key_suppliers],
            ["Relations", collab.relations],
          ].map(([label, value]) =>
            value ? (
              <div key={label as string} className="rounded-lg bg-plane p-2.5">
                <dt className="text-xs font-semibold text-ink-muted">{label}</dt>
                <dd>{value}</dd>
              </div>
            ) : null,
          )}
        </dl>
        {!collab.direct_reports && !collab.relations && (profile.collaboration_text || "—")}
      </Section>
      <Section title="Authorities">{profile.authorities_text || "—"}</Section>
      <Section title="General Working Condition">{profile.working_conditions || "—"}</Section>
      <Section title="Performance Standards">{profile.performance_standards || "—"}</Section>
      <Section title="Signoff">
        <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
          {["Line Manager", "Functional Manager", "OA", "HoD", "CHRO (if required)", "CEO/COO (if required)"].map((role) => (
            <div key={role} className="rounded-lg border border-dashed border-black/15 p-2.5 text-xs text-ink-muted">{role}:</div>
          ))}
        </div>
      </Section>
    </div>
  );
}

function Responsibilities({ profile }: { profile: Detail }) {
  if (profile.responsibilities.length === 0)
    return <div className="whitespace-pre-wrap text-sm text-ink-secondary">{profile.responsibilities_text || "No responsibilities recorded."}</div>;
  return (
    <ol className="space-y-2">
      {profile.responsibilities.map((r, i) => (
        <li key={r.id ?? i} className="flex gap-3 rounded-lg bg-plane p-3 text-sm">
          <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand text-xs font-bold text-brand-ink">{i + 1}</span>
          <div className="flex-1">
            {r.text}
            <div className="mt-1 flex flex-wrap gap-3 text-xs text-ink-muted">
              {r.pct_time != null && <span>{r.pct_time}% of time</span>}
              {r.frequency && <span>{r.frequency}</span>}
              {r.deliverables && <span>Deliverables: {r.deliverables}</span>}
              {r.decision_authority && <span>Decides: {r.decision_authority}</span>}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}

const LEVEL_ORDER = ["Basic", "Intermediate", "Advanced", "Expert"];

function Competencies({ profile }: { profile: Detail }) {
  const technical = profile.profile_competencies.filter((c) => c.competency.comp_type === "Technical");
  const behavioral = profile.profile_competencies.filter((c) => c.competency.comp_type === "Behavioral");
  const other = profile.profile_competencies.filter((c) => !["Technical", "Behavioral"].includes(c.competency.comp_type));
  return (
    <div className="space-y-6">
      <div>
        <h3 className="mb-2 text-sm font-bold">Technical competencies ({technical.length})</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase text-ink-muted">
              <tr><th className="py-1.5 pr-3">Title</th><th className="py-1.5 pr-3">Type</th><th className="py-1.5 pr-3">Required level</th><th className="py-1.5">Assessment</th></tr>
            </thead>
            <tbody>
              {technical.map((c) => (
                <tr key={c.id} className="border-t border-black/5">
                  <td className="py-1.5 pr-3 font-medium">{c.competency.name}</td>
                  <td className="py-1.5 pr-3 text-ink-secondary">{c.competency.category || "Technical"}</td>
                  <td className="py-1.5 pr-3">
                    <LevelDots level={c.required_level} />
                  </td>
                  <td className="py-1.5 text-xs text-ink-muted">{c.assessment_method}</td>
                </tr>
              ))}
              {technical.length === 0 && <tr><td colSpan={4} className="py-3 text-ink-muted">None recorded.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
      <div>
        <h3 className="mb-2 text-sm font-bold">Behavioral competencies (Live Y'ello)</h3>
        <div className="flex flex-wrap gap-2">
          {behavioral.map((c) => (
            <span key={c.id} className="rounded-full bg-brand/25 px-3 py-1 text-sm font-medium text-brand-ink">{c.competency.name}</span>
          ))}
          {behavioral.length === 0 && <span className="text-sm text-ink-muted">{profile.behavioral_text || "None recorded."}</span>}
        </div>
      </div>
      {other.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-bold">Other competencies</h3>
          <div className="flex flex-wrap gap-2">
            {other.map((c) => (
              <span key={c.id} className="rounded-full bg-plane px-3 py-1 text-sm">{c.competency.comp_type}: {c.competency.name} {c.required_level && `· ${c.required_level}`}</span>
            ))}
          </div>
        </div>
      )}
      {profile.profile_skills.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-bold">Skills matrix</h3>
          <div className="grid gap-2 md:grid-cols-2">
            {profile.profile_skills.map((s) => (
              <div key={s.id} className="flex items-center justify-between rounded-lg bg-plane px-3 py-2 text-sm">
                <span>{s.skill.name} <span className="text-xs text-ink-muted">({s.requirement})</span></span>
                <span className="tabular-nums text-ink-secondary">{s.level}/5</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function LevelDots({ level }: { level: string }) {
  const idx = LEVEL_ORDER.indexOf(level);
  if (idx < 0) return <span className="text-sm">{level || "—"}</span>;
  return (
    <span className="inline-flex items-center gap-1" title={level}>
      {LEVEL_ORDER.map((l, i) => (
        <span key={l} className={`h-2 w-2 rounded-full ${i <= idx ? "bg-series-1" : "bg-grid"}`} />
      ))}
      <span className="ml-1 text-xs text-ink-secondary">{level}</span>
    </span>
  );
}

const QUAL_LABELS: Record<string, string> = {
  education: "Education", experience: "Experience", certification: "Professional Certifications",
  language: "Languages", software: "Software Knowledge", license: "Licenses",
  training: "Trainings", preferred: "Preferred Qualifications",
};

function Qualifications({ profile }: { profile: Detail }) {
  const groups = new Map<string, typeof profile.qualifications>();
  for (const q of profile.qualifications) {
    groups.set(q.qual_type, [...(groups.get(q.qual_type) ?? []), q]);
  }
  return (
    <div className="space-y-4">
      {[...groups.entries()].map(([type, quals]) => (
        <Section key={type} title={QUAL_LABELS[type] ?? type}>
          {quals.map((q, i) => (
            <p key={q.id ?? i} className="mb-1">
              {q.text} {!q.mandatory && <span className="text-xs text-ink-muted">(preferred)</span>}
            </p>
          ))}
        </Section>
      ))}
      {groups.size === 0 && <div className="text-sm text-ink-muted">No qualifications recorded.</div>}
      {profile.kpis.length > 0 && (
        <Section title="KPIs">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase text-ink-muted">
              <tr><th className="py-1 pr-3">KPI</th><th className="py-1 pr-3">Type</th><th className="py-1 pr-3">Weight</th><th className="py-1">Measurement</th></tr>
            </thead>
            <tbody>
              {profile.kpis.map((k, i) => (
                <tr key={k.id ?? i} className="border-t border-black/5">
                  <td className="py-1.5 pr-3">{k.name}</td>
                  <td className="py-1.5 pr-3">{k.kpi_type}</td>
                  <td className="py-1.5 pr-3 tabular-nums">{k.weight != null ? `${k.weight}%` : "—"}</td>
                  <td className="py-1.5 text-xs text-ink-muted">{k.measurement_method}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}
    </div>
  );
}

function CareerPath({ profile }: { profile: Detail }) {
  const [edges, setEdges] = useState<CareerEdge[] | null>(null);
  useEffect(() => {
    api<CareerEdge[]>(`/api/profiles/${profile.id}/career-path`).then(setEdges).catch(() => setEdges([]));
  }, [profile.id]);
  if (!edges) return <div className="text-ink-muted">Loading…</div>;
  const next = edges.filter((e) => e.direction === "outgoing" && e.path_type === "next");
  const previous = edges.filter((e) => e.direction === "incoming" && e.path_type === "next");
  const lateral = edges.filter((e) => e.path_type === "lateral");
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <CareerColumn title="← Previous roles (feeder)" edges={previous} empty="No feeder roles mapped." />
      <div className="rounded-xl border-2 border-brand bg-brand/10 p-4 text-center">
        <div className="text-xs font-semibold uppercase text-ink-muted">Current role</div>
        <div className="mt-1 font-bold">{profile.job_title}</div>
        <div className="text-sm text-ink-secondary">Level {profile.grade?.code ?? profile.org_level}</div>
      </div>
      <CareerColumn title="Next roles →" edges={next} empty="No next roles mapped yet." />
      {lateral.length > 0 && (
        <div className="md:col-span-3">
          <CareerColumn title="Lateral moves" edges={lateral} empty="" />
        </div>
      )}
    </div>
  );
}

function CareerColumn({ title, edges, empty }: { title: string; edges: CareerEdge[]; empty: string }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-bold">{title}</h3>
      <div className="space-y-2">
        {edges.map((e) => (
          <Link key={e.id + e.direction} to={`/profiles/${e.profile_id}`} className="block rounded-lg border border-black/10 bg-white p-3 text-sm hover:border-series-1">
            <div className="font-medium">{e.title}</div>
            <div className="text-xs text-ink-muted">Level {e.grade || "—"} {e.readiness_level && `· ${e.readiness_level}`}</div>
          </Link>
        ))}
        {edges.length === 0 && empty && <div className="text-sm text-ink-muted">{empty}</div>}
      </div>
    </div>
  );
}

const WORKFLOW_ACTIONS: { action: string; label: string; kind: "primary" | "ghost" | "danger" }[] = [
  { action: "submit", label: "Submit for review", kind: "primary" },
  { action: "approve", label: "Approve → next stage", kind: "primary" },
  { action: "publish", label: "Publish", kind: "primary" },
  { action: "reject", label: "Reject to Draft", kind: "danger" },
  { action: "request_change", label: "Request changes", kind: "ghost" },
  { action: "archive", label: "Archive", kind: "ghost" },
  { action: "restore", label: "Restore", kind: "ghost" },
];

function Workflow({ profile, user, onChange }: { profile: Detail; user: User; onChange: () => void }) {
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [versions, setVersions] = useState<Version[]>([]);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api<WorkflowEvent[]>(`/api/profiles/${profile.id}/workflow`).then(setEvents).catch(() => {});
    api<Version[]>(`/api/profiles/${profile.id}/versions`).then(setVersions).catch(() => {});
  }, [profile.id]);
  useEffect(load, [load]);

  async function run(action: string) {
    setError("");
    try {
      await api(`/api/profiles/${profile.id}/workflow`, {
        method: "POST",
        body: JSON.stringify({ action, comment, signature: comment ? `signed:${user.username}` : "" }),
      });
      setComment("");
      onChange();
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <h3 className="mb-2 text-sm font-bold">Actions — current state: {profile.status}</h3>
        <textarea
          className="input mb-2"
          rows={2}
          placeholder="Comment / digital signature note (optional)"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
        <div className="flex flex-wrap gap-2">
          {WORKFLOW_ACTIONS.map((a) => (
            <button
              key={a.action}
              className={a.kind === "primary" ? "btn-primary" : a.kind === "danger" ? "btn bg-status-critical text-white hover:bg-red-700" : "btn-ghost"}
              onClick={() => run(a.action)}
            >
              {a.label}
            </button>
          ))}
          <button className="btn-ghost" onClick={() => run("comment")}>Add comment only</button>
        </div>
        {error && <div className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-status-critical">{error}</div>}
        <p className="mt-2 text-xs text-ink-muted">
          Review chain: Draft → Under Review → HR Review → Business Review → Organization Design Review →
          Compensation Review → Executive Approval → Published. Invalid transitions are rejected by the server.
        </p>

        <h3 className="mb-2 mt-6 text-sm font-bold">Version history</h3>
        <ul className="space-y-1.5 text-sm">
          {versions.map((v) => (
            <li key={v.id} className="flex items-center justify-between rounded-lg bg-plane px-3 py-2">
              <span>v{v.version_no} — {v.change_note || "No note"}</span>
              <span className="text-xs text-ink-muted">{v.changed_by} · {new Date(v.created_at).toLocaleString()}</span>
            </li>
          ))}
          {versions.length === 0 && <li className="text-ink-muted">No versions yet.</li>}
        </ul>
      </div>
      <div>
        <h3 className="mb-2 text-sm font-bold">Activity trail</h3>
        <ul className="space-y-2">
          {events.map((e) => (
            <li key={e.id} className="rounded-lg border border-black/5 p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">
                  {e.event_type === "comment" ? "💬 Comment" : e.event_type === "signature" ? "✍️ Signed transition" : e.event_type === "change_request" ? "🔁 Change request" : "→ Transition"}
                  {e.to_state && <span className="text-ink-secondary"> {e.from_state || "•"} → {e.to_state}</span>}
                </span>
                <span className="text-xs text-ink-muted">{new Date(e.created_at).toLocaleString()}</span>
              </div>
              <div className="text-xs text-ink-muted">{e.actor} ({e.actor_role})</div>
              {e.comment && <div className="mt-1 text-ink-secondary">{e.comment}</div>}
            </li>
          ))}
          {events.length === 0 && <li className="text-sm text-ink-muted">No workflow activity yet.</li>}
        </ul>
      </div>
    </div>
  );
}

function AIPanel({ profile }: { profile: Detail }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "ai"; text: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [similar, setSimilar] = useState<{ id: number; job_title: string; similarity: number; grade: string }[]>([]);

  useEffect(() => {
    api<typeof similar>(`/api/ai/similar/${profile.id}?top=6`).then(setSimilar).catch(() => {});
  }, [profile.id]);

  async function ask(task: string, q?: string) {
    setBusy(true);
    const label = q ?? task.replaceAll("_", " ");
    setMessages((m) => [...m, { role: "user", text: label }]);
    try {
      const res = await api<{ provider: string; result: unknown }>("/api/ai", {
        method: "POST",
        body: JSON.stringify({ task, profile_id: profile.id, question: q }),
      });
      const text = typeof res.result === "string" ? res.result : JSON.stringify(res.result, null, 2);
      setMessages((m) => [...m, { role: "ai", text: `[${res.provider}] ${text}` }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "ai", text: `Error: ${(e as Error).message}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <div className="mb-3 flex flex-wrap gap-2">
          {[
            ["executive_summary", "Executive summary"],
            ["recommend_competencies", "Recommend competencies"],
            ["find_missing_skills", "Find missing skills"],
            ["suggest_career_path", "Suggest career path"],
            ["estimate_grade", "Estimate grade"],
            ["benchmark", "Benchmark"],
            ["suggest_learning", "Suggest learning"],
          ].map(([task, label]) => (
            <button key={task} className="btn-ghost" disabled={busy} onClick={() => ask(task)}>{label}</button>
          ))}
        </div>
        <div className="mb-3 max-h-96 space-y-2 overflow-auto rounded-xl bg-plane p-3">
          {messages.length === 0 && (
            <div className="p-4 text-sm text-ink-muted">
              Ask anything about this profile — “What competencies should this role have?”,
              “What career path follows this role?”, “What grade fits this role?”
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`max-w-[85%] whitespace-pre-wrap rounded-xl px-3 py-2 text-sm ${m.role === "user" ? "ml-auto bg-brand-ink text-white" : "bg-white shadow-sm"}`}>
              {m.text}
            </div>
          ))}
          {busy && <div className="text-sm text-ink-muted">Thinking…</div>}
        </div>
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (question.trim()) {
              ask("chat", question.trim());
              setQuestion("");
            }
          }}
        >
          <input className="input" placeholder="Chat with this job profile…" value={question} onChange={(e) => setQuestion(e.target.value)} />
          <button className="btn-brand" disabled={busy} type="submit">Ask</button>
        </form>
      </div>
      <div>
        <h3 className="mb-2 text-sm font-bold">Similar profiles</h3>
        <div className="space-y-2">
          {similar.map((s) => (
            <Link key={s.id} to={`/profiles/${s.id}`} className="block rounded-lg border border-black/10 p-2.5 text-sm hover:border-series-1">
              <div className="font-medium">{s.job_title}</div>
              <div className="text-xs text-ink-muted">Level {s.grade || "—"} · similarity {(s.similarity * 100).toFixed(0)}%</div>
            </Link>
          ))}
          {similar.length === 0 && <div className="text-sm text-ink-muted">No similar profiles found.</div>}
        </div>
      </div>
    </div>
  );
}

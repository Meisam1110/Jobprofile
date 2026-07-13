import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { KPI, ProfileDetail, Qualification, Responsibility, Taxonomy, api } from "../api";

interface CompetencyRow { name: string; comp_type: string; category: string; required_level: string; desired_level: string; importance: string; assessment_method: string }
interface SkillRow { name: string; requirement: string; level: number; category: string }

const EMPTY_RESP: Responsibility = { text: "", pct_time: null, frequency: "", key_tasks: "", deliverables: "", decision_authority: "", sort_order: 0 };
const EMPTY_KPI: KPI = { name: "", kpi_type: "Individual", weight: null, owner: "", formula: "", measurement_method: "" };

export default function ProfileEdit() {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();
  const [taxonomy, setTaxonomy] = useState<Taxonomy | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);

  const [form, setForm] = useState({
    job_title: "", job_code: "", location: "", reports_to: "", direct_reports: 0,
    employment_type: "Full-time", grade_code: "", division: "", department: "",
    role_family: "", job_family: "", sub_family: "", language: "en",
    mission: "", context: "", authorities_text: "As per Delegation of authority",
    education_text: "", experience_text: "", trainings_text: "",
    working_conditions: "General MTNIrancell working conditions",
    performance_standards: "As per performance agreement",
    collaboration_text: "", change_note: "",
  });
  const [responsibilities, setResponsibilities] = useState<Responsibility[]>([{ ...EMPTY_RESP }]);
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [competencies, setCompetencies] = useState<CompetencyRow[]>([]);
  const [skills, setSkills] = useState<SkillRow[]>([]);
  const [qualifications, setQualifications] = useState<Qualification[]>([]);

  useEffect(() => {
    api<Taxonomy>("/api/taxonomy").then(setTaxonomy).catch(() => {});
    if (!isNew) {
      api<ProfileDetail>(`/api/profiles/${id}`).then((p) => {
        setForm((f) => ({
          ...f,
          job_title: p.job_title, job_code: p.job_code, location: p.location,
          reports_to: p.reports_to, direct_reports: p.direct_reports,
          employment_type: p.employment_type, grade_code: p.grade?.code ?? "",
          division: p.division?.name ?? "", department: p.department?.name ?? "",
          role_family: p.role_family?.name ?? "", job_family: p.job_family?.name ?? "",
          sub_family: p.sub_family, language: p.language, mission: p.mission, context: p.context,
          authorities_text: p.authorities_text, education_text: p.education_text,
          experience_text: p.experience_text, trainings_text: p.trainings_text,
          working_conditions: p.working_conditions, performance_standards: p.performance_standards,
          collaboration_text: p.collaboration_text,
        }));
        setResponsibilities(p.responsibilities.length ? p.responsibilities : [{ ...EMPTY_RESP }]);
        setKpis(p.kpis);
        setCompetencies(
          p.profile_competencies.map((c) => ({
            name: c.competency.name, comp_type: c.competency.comp_type, category: c.competency.category,
            required_level: c.required_level, desired_level: c.desired_level,
            importance: c.importance, assessment_method: c.assessment_method,
          })),
        );
        setSkills(p.profile_skills.map((s) => ({ name: s.skill.name, requirement: s.requirement, level: s.level, category: s.skill.category })));
        setQualifications(p.qualifications);
      }).catch((e) => setError(e.message));
    }
  }, [id, isNew]);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function aiDraft() {
    if (!form.job_title) return setError("Enter a job title first — the AI drafts from it.");
    setAiBusy(true);
    setError("");
    try {
      const res = await api<{ result: Record<string, unknown> }>("/api/ai", {
        method: "POST",
        body: JSON.stringify({ task: "generate_profile", job_title: form.job_title }),
      });
      const r = res.result;
      if (typeof r !== "object" || r === null) throw new Error("Unexpected AI response");
      setForm((f) => ({
        ...f,
        mission: String(r.mission ?? f.mission),
        context: String(r.context ?? f.context),
        education_text: String(r.education ?? f.education_text),
        experience_text: String(r.experience ?? f.experience_text),
        trainings_text: String(r.trainings ?? f.trainings_text),
        working_conditions: String(r.working_conditions ?? f.working_conditions),
        performance_standards: String(r.performance_standards ?? f.performance_standards),
        grade_code: String(r.suggested_grade ?? f.grade_code ?? ""),
      }));
      if (Array.isArray(r.responsibilities))
        setResponsibilities(r.responsibilities.map((t: unknown, i: number) => ({ ...EMPTY_RESP, text: String(t), sort_order: i })));
      if (Array.isArray(r.technical_competencies))
        setCompetencies((prev) => [
          ...(r.technical_competencies as { name: string; category?: string; required_level?: string }[]).map((c) => ({
            name: c.name, comp_type: "Technical", category: c.category ?? "", required_level: c.required_level ?? "Intermediate",
            desired_level: "", importance: "", assessment_method: "Interview / Technical Assessment",
          })),
          ...prev.filter((c) => c.comp_type !== "Technical"),
        ]);
      if (Array.isArray(r.behavioral_competencies))
        setCompetencies((prev) => [
          ...prev.filter((c) => c.comp_type !== "Behavioral"),
          ...(r.behavioral_competencies as string[]).map((name) => ({
            name, comp_type: "Behavioral", category: "", required_level: "Expected",
            desired_level: "", importance: "", assessment_method: "Behavioral Interview",
          })),
        ]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setAiBusy(false);
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    const payload = {
      ...form,
      direct_reports: Number(form.direct_reports) || 0,
      responsibilities: responsibilities.filter((r) => r.text.trim()),
      kpis: kpis.filter((k) => k.name.trim()),
      competencies: competencies.filter((c) => c.name.trim()),
      skills: skills.filter((s) => s.name.trim()),
      qualifications: qualifications.filter((q) => q.text.trim()),
    };
    try {
      const saved = await api<ProfileDetail>(isNew ? "/api/profiles" : `/api/profiles/${id}`, {
        method: isNew ? "POST" : "PUT",
        body: JSON.stringify(payload),
      });
      navigate(`/profiles/${saved.id}`);
    } catch (err) {
      setError((err as Error).message);
      setSaving(false);
    }
  }

  return (
    <form className="mx-auto max-w-5xl space-y-4" onSubmit={submit}>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{isNew ? "New job profile" : `Edit: ${form.job_title}`}</h1>
        <div className="flex gap-2">
          <button type="button" className="btn-brand" disabled={aiBusy} onClick={aiDraft}>
            {aiBusy ? "Drafting…" : "✨ AI draft from title"}
          </button>
          <button type="button" className="btn-ghost" onClick={() => navigate(-1)}>Cancel</button>
          <button className="btn-primary" disabled={saving} type="submit">{saving ? "Saving…" : "Save profile"}</button>
        </div>
      </div>
      {error && <div className="card p-3 text-sm text-status-critical">{error}</div>}

      <Card title="Job information (template header)">
        <div className="grid gap-3 md:grid-cols-3">
          <Field label="Title of Position *"><input required className="input" value={form.job_title} onChange={(e) => set("job_title", e.target.value)} /></Field>
          <Field label="Location of the Job"><input className="input" value={form.location} onChange={(e) => set("location", e.target.value)} /></Field>
          <Field label="Reports to"><input className="input" value={form.reports_to} onChange={(e) => set("reports_to", e.target.value)} /></Field>
          <Field label="Number of subordinates"><input type="number" min={0} className="input" value={form.direct_reports} onChange={(e) => set("direct_reports", Number(e.target.value))} /></Field>
          <Field label="Level">
            <select className="input" value={form.grade_code} onChange={(e) => set("grade_code", e.target.value)}>
              <option value="">—</option>
              {taxonomy?.grades.map((g) => <option key={g.id} value={g.code}>{g.code} — {g.band}</option>)}
            </select>
          </Field>
          <Field label="Employment type">
            <select className="input" value={form.employment_type} onChange={(e) => set("employment_type", e.target.value)}>
              {["Full-time", "Part-time", "Contractor", "Vendor", "Consultant"].map((t) => <option key={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Division">
            <input className="input" list="divisions" value={form.division} onChange={(e) => set("division", e.target.value)} />
            <datalist id="divisions">{taxonomy?.divisions.map((d) => <option key={d.id} value={d.name} />)}</datalist>
          </Field>
          <Field label="Department"><input className="input" value={form.department} onChange={(e) => set("department", e.target.value)} /></Field>
          <Field label="Job family">
            <input className="input" list="jobfams" value={form.job_family} onChange={(e) => set("job_family", e.target.value)} />
            <datalist id="jobfams">{taxonomy?.job_families.slice(0, 200).map((d) => <option key={d.id} value={d.name} />)}</datalist>
          </Field>
        </div>
      </Card>

      <Card title="Mission & Context">
        <Field label="Mission"><textarea className="input" rows={3} value={form.mission} onChange={(e) => set("mission", e.target.value)} /></Field>
        <Field label="Context"><textarea className="input" rows={3} value={form.context} onChange={(e) => set("context", e.target.value)} /></Field>
      </Card>

      <Card title={`Roles & Responsibilities (${responsibilities.length})`}>
        {responsibilities.map((r, i) => (
          <div key={i} className="mb-2 flex gap-2">
            <textarea
              className="input" rows={2} placeholder={`Responsibility ${i + 1}`}
              value={r.text}
              onChange={(e) => setResponsibilities((list) => list.map((x, j) => (j === i ? { ...x, text: e.target.value } : x)))}
            />
            <input
              className="input w-20" type="number" placeholder="%" min={0} max={100}
              value={r.pct_time ?? ""}
              onChange={(e) => setResponsibilities((list) => list.map((x, j) => (j === i ? { ...x, pct_time: e.target.value ? Number(e.target.value) : null } : x)))}
              title="Percentage of time"
            />
            <button type="button" className="btn-ghost" onClick={() => setResponsibilities((list) => list.filter((_, j) => j !== i))}>✕</button>
          </div>
        ))}
        <button type="button" className="btn-ghost" onClick={() => setResponsibilities((l) => [...l, { ...EMPTY_RESP, sort_order: l.length }])}>+ Add responsibility</button>
      </Card>

      <Card title={`Competencies (${competencies.length})`}>
        {competencies.map((c, i) => (
          <div key={i} className="mb-2 grid grid-cols-12 gap-2">
            <input className="input col-span-5" placeholder="Competency" value={c.name} onChange={(e) => setCompetencies((l) => l.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))} />
            <select className="input col-span-3" value={c.comp_type} onChange={(e) => setCompetencies((l) => l.map((x, j) => (j === i ? { ...x, comp_type: e.target.value } : x)))}>
              {taxonomy?.competency_types.map((t) => <option key={t}>{t}</option>)}
            </select>
            <select className="input col-span-3" value={c.required_level} onChange={(e) => setCompetencies((l) => l.map((x, j) => (j === i ? { ...x, required_level: e.target.value } : x)))}>
              <option value="">Level…</option>
              {[...(taxonomy?.competency_levels ?? []), "Expected"].map((t) => <option key={t}>{t}</option>)}
            </select>
            <button type="button" className="btn-ghost col-span-1" onClick={() => setCompetencies((l) => l.filter((_, j) => j !== i))}>✕</button>
          </div>
        ))}
        <button type="button" className="btn-ghost" onClick={() => setCompetencies((l) => [...l, { name: "", comp_type: "Technical", category: "", required_level: "Intermediate", desired_level: "", importance: "", assessment_method: "" }])}>+ Add competency</button>
      </Card>

      <Card title={`KPIs (${kpis.length})`}>
        {kpis.map((k, i) => (
          <div key={i} className="mb-2 grid grid-cols-12 gap-2">
            <input className="input col-span-5" placeholder="KPI name" value={k.name} onChange={(e) => setKpis((l) => l.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))} />
            <select className="input col-span-3" value={k.kpi_type} onChange={(e) => setKpis((l) => l.map((x, j) => (j === i ? { ...x, kpi_type: e.target.value } : x)))}>
              {["Individual", "Team", "Department", "Strategic"].map((t) => <option key={t}>{t}</option>)}
            </select>
            <input className="input col-span-2" type="number" placeholder="Weight %" value={k.weight ?? ""} onChange={(e) => setKpis((l) => l.map((x, j) => (j === i ? { ...x, weight: e.target.value ? Number(e.target.value) : null } : x)))} />
            <button type="button" className="btn-ghost col-span-1" onClick={() => setKpis((l) => l.filter((_, j) => j !== i))}>✕</button>
          </div>
        ))}
        <button type="button" className="btn-ghost" onClick={() => setKpis((l) => [...l, { ...EMPTY_KPI }])}>+ Add KPI</button>
      </Card>

      <Card title="Job requirements">
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Education"><textarea className="input" rows={3} value={form.education_text} onChange={(e) => set("education_text", e.target.value)} /></Field>
          <Field label="Experience"><textarea className="input" rows={3} value={form.experience_text} onChange={(e) => set("experience_text", e.target.value)} /></Field>
          <Field label="Trainings"><textarea className="input" rows={2} value={form.trainings_text} onChange={(e) => set("trainings_text", e.target.value)} /></Field>
          <Field label="Authorities"><textarea className="input" rows={2} value={form.authorities_text} onChange={(e) => set("authorities_text", e.target.value)} /></Field>
          <Field label="General working condition"><textarea className="input" rows={2} value={form.working_conditions} onChange={(e) => set("working_conditions", e.target.value)} /></Field>
          <Field label="Performance standards"><textarea className="input" rows={2} value={form.performance_standards} onChange={(e) => set("performance_standards", e.target.value)} /></Field>
        </div>
        <Field label="Collaboration (Direct Reports / Matrix Reports / Key Customers / Key Suppliers)">
          <textarea className="input" rows={2} value={form.collaboration_text} onChange={(e) => set("collaboration_text", e.target.value)} />
        </Field>
      </Card>

      <Card title="Change note">
        <input className="input" placeholder="What changed and why (stored in version history)" value={form.change_note} onChange={(e) => set("change_note", e.target.value)} />
      </Card>

      <div className="flex justify-end gap-2 pb-8">
        <button type="button" className="btn-ghost" onClick={() => navigate(-1)}>Cancel</button>
        <button className="btn-primary" disabled={saving} type="submit">{saving ? "Saving…" : "Save profile"}</button>
      </div>
    </form>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-4">
      <h2 className="mb-3 text-sm font-bold">{title}</h2>
      {children}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-2">
      <label className="label">{label}</label>
      {children}
    </div>
  );
}

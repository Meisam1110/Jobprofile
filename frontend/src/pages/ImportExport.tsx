import { useState } from "react";
import { api, currentUser } from "../api";

export default function ImportExport() {
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const user = currentUser();

  async function importMaster() {
    setBusy(true);
    setError("");
    try {
      setStats(await api("/api/import/master", { method: "POST" }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function uploadFile(file: File) {
    setBusy(true);
    setError("");
    const body = new FormData();
    body.append("file", file);
    try {
      const response = await fetch("/api/import/excel", {
        method: "POST",
        headers: { Authorization: `Bearer ${user?.token ?? ""}` },
        body,
      });
      if (!response.ok) throw new Error((await response.json()).detail ?? response.statusText);
      setStats(await response.json());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div>
        <h1 className="text-xl font-bold">Import & Export</h1>
        <p className="text-sm text-ink-muted">Bulk data flows in the master-workbook format. Re-imports update existing profiles (matched by source file) — no duplicates.</p>
      </div>

      <div className="card p-5">
        <h2 className="mb-1 text-sm font-bold">Import the bundled Irancell master workbook</h2>
        <p className="mb-3 text-sm text-ink-muted">Loads/refreshes all profiles from <code>data/job_profiles_master.xlsm</code> shipped with the app.</p>
        <button className="btn-brand" disabled={busy} onClick={importMaster}>{busy ? "Importing…" : "Import master workbook"}</button>
      </div>

      <div className="card p-5">
        <h2 className="mb-1 text-sm font-bold">Bulk upload an Excel workbook</h2>
        <p className="mb-3 text-sm text-ink-muted">
          Same sheet layout as the master file (<code>Job_Profile_Data</code>, header on row 8) —
          or <a className="text-series-1 underline" href="/api/import/template">download the blank import template</a>.
        </p>
        <input
          type="file"
          accept=".xlsx,.xlsm"
          disabled={busy}
          onChange={(e) => e.target.files?.[0] && uploadFile(e.target.files[0])}
          className="text-sm"
        />
      </div>

      {stats && (
        <div className="card bg-green-50 p-4 text-sm">
          <strong>Import complete.</strong> Created {stats.created}, updated {stats.updated}, skipped {stats.skipped};
          {" "}{stats.competencies} competency assignments parsed.
        </div>
      )}
      {error && <div className="card p-4 text-sm text-status-critical">{error}</div>}

      <div className="card p-5">
        <h2 className="mb-1 text-sm font-bold">Export</h2>
        <p className="mb-3 text-sm text-ink-muted">Individual profiles export to PDF / Word / JSON from their page. Bulk export:</p>
        <div className="flex flex-wrap gap-2">
          <a className="btn-primary" href="/api/export/excel">Export all profiles to Excel</a>
          <a className="btn-ghost" href="/api/export/excel?status=Published">Published only</a>
        </div>
      </div>

      <div className="card p-5 text-sm text-ink-muted">
        <h2 className="mb-1 text-sm font-bold text-ink">API import</h2>
        Programmatic access uses the same REST API (see <code>/docs</code>): <code>POST /api/profiles</code> per profile,
        or <code>POST /api/import/excel</code> with a workbook. Word/PDF AI-assisted extraction is available through the
        AI Assistant’s “Convert existing JD” task.
      </div>
    </div>
  );
}

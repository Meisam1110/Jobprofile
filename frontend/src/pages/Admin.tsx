import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

interface AuditRow { id: number; actor: string; action: string; entity: string; entity_id: string; detail: Record<string, unknown>; created_at: string }
interface DupRow { a_id: number; a_title: string; b_id: number; b_title: string; score: number }

export default function Admin() {
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [dups, setDups] = useState<DupRow[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [scan, setScan] = useState<{ review_due: number; expired: number } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<AuditRow[]>("/api/admin/audit").then(setAudit).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Administration</h1>
        <p className="text-sm text-ink-muted">Audit trail, data quality and housekeeping. Role-based permissions: employee &lt; manager &lt; hr &lt; admin.</p>
      </div>
      {error && <div className="card p-4 text-sm text-status-critical">{error} (admin role required)</div>}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h2 className="mb-2 text-sm font-bold">Duplicate detection</h2>
          <p className="mb-3 text-xs text-ink-muted">Finds pairs of highly similar active profiles (TF-IDF ≥ 0.82).</p>
          <button
            className="btn-primary"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              api<DupRow[]>("/api/analytics/duplicates").then(setDups).catch((e) => setError(e.message)).finally(() => setBusy(false));
            }}
          >
            {busy ? "Scanning…" : "Scan for duplicates"}
          </button>
          {dups && (
            <ul className="mt-3 max-h-72 space-y-1.5 overflow-auto text-sm">
              {dups.map((d) => (
                <li key={`${d.a_id}-${d.b_id}`} className="rounded-lg bg-plane p-2.5">
                  <Link className="font-medium hover:underline" to={`/profiles/${d.a_id}`}>{d.a_title}</Link>
                  <span className="mx-1 text-ink-muted">↔</span>
                  <Link className="font-medium hover:underline" to={`/profiles/${d.b_id}`}>{d.b_title}</Link>
                  <span className="ml-2 text-xs text-ink-muted">{(d.score * 100).toFixed(0)}% similar</span>
                </li>
              ))}
              {dups.length === 0 && <li className="text-ink-muted">No duplicates above threshold.</li>}
            </ul>
          )}
        </div>

        <div className="card p-4">
          <h2 className="mb-2 text-sm font-bold">Review housekeeping</h2>
          <p className="mb-3 text-xs text-ink-muted">Scans for profiles overdue for review (&gt;2 years) and raises notifications for HR.</p>
          <button
            className="btn-primary"
            onClick={() => api<typeof scan>("/api/admin/review-scan", { method: "POST" }).then(setScan).catch((e) => setError(e.message))}
          >
            Run review scan
          </button>
          {scan && (
            <div className="mt-3 rounded-lg bg-plane p-3 text-sm">
              {scan.review_due} profiles due for review · {scan.expired} expired (&gt;2y since approval).
            </div>
          )}
          <h2 className="mb-2 mt-6 text-sm font-bold">Backup & restore</h2>
          <p className="text-xs text-ink-muted">
            SQLite: copy <code>backend/jobprofile.db</code>. PostgreSQL: <code>pg_dump</code> on a schedule.
            Full data also exports via <a className="text-series-1 underline" href="/api/export/excel">Excel</a> and per-profile JSON.
          </p>
        </div>
      </div>

      <div className="card overflow-hidden">
        <h2 className="border-b border-black/10 px-4 py-3 text-sm font-bold">Audit log (latest {audit.length})</h2>
        <table className="w-full text-sm">
          <thead className="bg-plane text-left text-xs uppercase text-ink-muted">
            <tr><th className="px-4 py-2">When</th><th className="px-3 py-2">Actor</th><th className="px-3 py-2">Action</th><th className="px-3 py-2">Entity</th><th className="px-3 py-2">Detail</th></tr>
          </thead>
          <tbody>
            {audit.map((row) => (
              <tr key={row.id} className="border-t border-black/5">
                <td className="whitespace-nowrap px-4 py-1.5 text-xs text-ink-muted">{new Date(row.created_at).toLocaleString()}</td>
                <td className="px-3 py-1.5">{row.actor}</td>
                <td className="px-3 py-1.5 font-medium">{row.action}</td>
                <td className="px-3 py-1.5 text-ink-secondary">{row.entity} {row.entity_id && `#${row.entity_id}`}</td>
                <td className="max-w-64 truncate px-3 py-1.5 text-xs text-ink-muted">{JSON.stringify(row.detail)}</td>
              </tr>
            ))}
            {audit.length === 0 && <tr><td colSpan={5} className="px-4 py-6 text-center text-ink-muted">No audit entries (or admin role required).</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

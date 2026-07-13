import { FormEvent, useState } from "react";
import { User, api } from "../api";

const DEMO_ROLES = [
  { username: "hr", label: "HR / Organization Architecture", blurb: "Create, edit, approve, publish, import" },
  { username: "manager", label: "Line Manager", blurb: "Review team profiles, approve changes" },
  { username: "employee", label: "Employee", blurb: "View profiles, career paths, suggest changes" },
  { username: "admin", label: "Administrator", blurb: "Everything + audit logs and configuration" },
];

export default function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [username, setUsername] = useState("hr");
  const [password, setPassword] = useState("demo");
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const user = await api<User>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      onLogin(user);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-ink p-6">
      <div className="w-full max-w-3xl overflow-hidden rounded-2xl bg-white shadow-2xl md:grid md:grid-cols-2">
        <div className="bg-brand p-8 text-brand-ink">
          <div className="text-3xl font-black">Job Profile Management</div>
          <div className="mt-1 text-sm font-semibold">MTN Irancell · Organization Architecture, HR</div>
          <p className="mt-6 text-sm leading-relaxed">
            The single source of truth for every job profile — job architecture, competencies,
            approval workflow, analytics and AI assistance, built on the official Irancell template.
          </p>
          <ul className="mt-6 space-y-2 text-sm">
            <li>• 1,400+ imported job profiles</li>
            <li>• Irancell levels 1 – 5 with 2H / 3H bands</li>
            <li>• Live Y'ello behavioral competencies</li>
            <li>• Line Manager → OA → HoD → CHRO signoff chain</li>
          </ul>
        </div>
        <form className="p-8" onSubmit={submit}>
          <h1 className="text-lg font-bold">Sign in</h1>
          <p className="mb-4 text-xs text-ink-muted">Demo build — password is “demo” for every role.</p>
          <label className="label" htmlFor="username">Role</label>
          <div className="mb-3 space-y-1.5">
            {DEMO_ROLES.map((r) => (
              <label
                key={r.username}
                className={`flex cursor-pointer items-start gap-2 rounded-lg border p-2.5 text-sm ${
                  username === r.username ? "border-brand-ink bg-plane" : "border-black/10"
                }`}
              >
                <input
                  type="radio"
                  name="role"
                  className="mt-0.5"
                  checked={username === r.username}
                  onChange={() => setUsername(r.username)}
                />
                <span>
                  <span className="font-semibold">{r.label}</span>
                  <span className="block text-xs text-ink-muted">{r.blurb}</span>
                </span>
              </label>
            ))}
          </div>
          <label className="label" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className="input mb-4"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-status-critical">{error}</div>}
          <button className="btn-primary w-full justify-center" type="submit">
            Sign in
          </button>
        </form>
      </div>
    </div>
  );
}

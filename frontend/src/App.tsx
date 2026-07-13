import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { Notification, User, api, currentUser, setUser } from "./api";
import Admin from "./pages/Admin";
import Assistant from "./pages/Assistant";
import Compare from "./pages/Compare";
import Dashboard from "./pages/Dashboard";
import ImportExport from "./pages/ImportExport";
import Login from "./pages/Login";
import ProfileDetail from "./pages/ProfileDetail";
import ProfileEdit from "./pages/ProfileEdit";
import Repository from "./pages/Repository";

const NAV = [
  { to: "/", label: "Dashboard", icon: "📊", roles: ["employee", "manager", "hr", "admin"] },
  { to: "/profiles", label: "Job Profiles", icon: "📁", roles: ["employee", "manager", "hr", "admin"] },
  { to: "/compare", label: "Compare", icon: "⚖️", roles: ["employee", "manager", "hr", "admin"] },
  { to: "/assistant", label: "AI Assistant", icon: "✨", roles: ["employee", "manager", "hr", "admin"] },
  { to: "/import-export", label: "Import / Export", icon: "🔁", roles: ["hr", "admin"] },
  { to: "/admin", label: "Administration", icon: "🛡️", roles: ["admin"] },
];

function Shell({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api<Notification[]>("/api/notifications").then(setNotifications).catch(() => {});
  }, []);
  const unread = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="flex min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-20 flex w-56 flex-col border-r border-black/10 bg-brand-ink text-white">
        <div className="flex items-center gap-2 px-4 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-lg font-black text-brand-ink">JP</div>
          <div>
            <div className="text-sm font-bold leading-tight">Job Profiles</div>
            <div className="text-[11px] text-white/60">MTN Irancell · OA, HR</div>
          </div>
        </div>
        <nav className="mt-2 flex-1 space-y-0.5 px-2">
          {NAV.filter((n) => n.roles.includes(user.role)).map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm ${
                  isActive ? "bg-brand text-brand-ink font-semibold" : "text-white/80 hover:bg-white/10"
                }`
              }
            >
              <span aria-hidden>{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/10 p-3 text-xs">
          <div className="font-semibold">{user.full_name}</div>
          <div className="capitalize text-white/60">{user.role}</div>
          <button className="mt-2 w-full rounded-md bg-white/10 px-2 py-1 text-white/80 hover:bg-white/20" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </aside>

      <div className="ml-56 flex-1">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-black/10 bg-surface/95 px-6 py-2.5 backdrop-blur">
          <GlobalSearch onPick={(id) => navigate(`/profiles/${id}`)} />
          <div className="relative">
            <button
              className="btn-ghost relative"
              onClick={() => setShowNotifs((s) => !s)}
              aria-label={`Notifications (${unread} unread)`}
            >
              🔔
              {unread > 0 && (
                <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-status-critical px-1 text-[10px] font-bold text-white">
                  {unread}
                </span>
              )}
            </button>
            {showNotifs && (
              <div className="absolute right-0 mt-2 max-h-96 w-96 overflow-auto rounded-xl border border-black/10 bg-white shadow-lg">
                {notifications.length === 0 && <div className="p-4 text-sm text-ink-muted">No notifications.</div>}
                {notifications.map((n) => (
                  <button
                    key={n.id}
                    className={`block w-full border-b border-black/5 px-4 py-2.5 text-left text-sm hover:bg-plane ${n.is_read ? "text-ink-muted" : ""}`}
                    onClick={() => {
                      api(`/api/notifications/${n.id}/read`, { method: "POST" }).catch(() => {});
                      setNotifications((list) => list.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
                      if (n.profile_id) navigate(`/profiles/${n.profile_id}`);
                      setShowNotifs(false);
                    }}
                  >
                    <span className="mr-1.5 rounded bg-plane px-1.5 py-0.5 text-[10px] font-semibold uppercase text-ink-secondary">
                      {n.notif_type.replaceAll("_", " ")}
                    </span>
                    {n.message}
                  </button>
                ))}
              </div>
            )}
          </div>
        </header>
        <main className="p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/profiles" element={<Repository />} />
            <Route path="/profiles/new" element={<ProfileEdit />} />
            <Route path="/profiles/:id" element={<ProfileDetail user={user} />} />
            <Route path="/profiles/:id/edit" element={<ProfileEdit />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/import-export" element={<ImportExport />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function GlobalSearch({ onPick }: { onPick: (id: number) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<{ id: number; job_title: string }[]>([]);
  useEffect(() => {
    if (q.length < 2) return setHits([]);
    const timer = setTimeout(() => {
      api<{ id: number; job_title: string }[]>(`/api/search/autocomplete?q=${encodeURIComponent(q)}`)
        .then(setHits)
        .catch(() => setHits([]));
    }, 200);
    return () => clearTimeout(timer);
  }, [q]);
  return (
    <div className="relative w-96">
      <input
        className="input"
        placeholder="Search job profiles…  (title, code, competency)"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      {hits.length > 0 && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-lg border border-black/10 bg-white shadow-lg">
          {hits.map((h) => (
            <button
              key={h.id}
              className="block w-full px-3 py-2 text-left text-sm hover:bg-plane"
              onClick={() => {
                setQ("");
                setHits([]);
                onPick(h.id);
              }}
            >
              {h.job_title}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [user, setUserState] = useState<User | null>(currentUser());
  if (!user) {
    return (
      <Login
        onLogin={(u) => {
          setUser(u);
          setUserState(u);
        }}
      />
    );
  }
  return (
    <Shell
      user={user}
      onLogout={() => {
        setUser(null);
        setUserState(null);
      }}
    />
  );
}

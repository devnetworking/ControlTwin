import { NavLink } from "react-router-dom";
import {
  Bell,
  ChevronLeft,
  ChevronRight,
  Cpu,
  PlusSquare,
  LayoutDashboard,
  Network,
  Radio,
  Settings,
  ShieldCheck,
  Building2,
  Users
} from "lucide-react";
import { useAlertStore } from "../../store/alertStore";
import { useAuth } from "../../hooks/useAuth";

const navGroups = [
  {
    title: "Operations",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/assets", label: "Assets", icon: Cpu },
      { to: "/assets/new", label: "Ajouter équipement", icon: PlusSquare },
      { to: "/topology", label: "Topology", icon: Network },
      { to: "/alerts", label: "Alerts", icon: Bell },
      { to: "/collectors", label: "Collectors", icon: Radio, minRole: "ot_analyst" }
    ]
  },
  {
    title: "Administration",
    minRole: "admin",
    items: [
      { to: "/users", label: "Users", icon: Users, minRole: "admin" },
      { to: "/sites", label: "Sites", icon: Building2, minRole: "admin" },
      { to: "/settings", label: "Settings", icon: Settings, minRole: "admin" }
    ]
  }
];

const ROLE_ORDER = ["viewer", "readonly", "ot_operator", "ot_analyst", "admin", "super_admin"];

export default function Sidebar({ collapsed, setCollapsed }) {
  const unread = useAlertStore((s) => s.unreadCount);
  const { role } = useAuth();

  const canAccess = (minRole) => !minRole || ROLE_ORDER.indexOf(role) >= ROLE_ORDER.indexOf(minRole);

  return (
    <aside
      className={`hidden md:flex md:flex-col border-r border-white/10 bg-gradient-to-b from-[#071021] via-[#0A162E] to-[#081328] transition-all duration-300 ${
        collapsed ? "w-20" : "w-72"
      }`}
    >
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-4">
        {!collapsed && (
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-ot-blue/80">ControlTwin</p>
            <h2 className="text-sm font-semibold text-white">Security Console</h2>
          </div>
        )}
        <button
          onClick={() => setCollapsed((v) => !v)}
          className="rounded-lg border border-white/10 bg-white/5 p-2 text-gray-200 transition hover:bg-white/10"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4">
        {navGroups
          .filter((group) => canAccess(group.minRole))
          .map((group) => (
            <div key={group.title} className="mb-5">
              {!collapsed && (
                <p className="mb-2 px-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  {group.title}
                </p>
              )}

              <div className="space-y-1">
                {group.items
                  .filter((item) => canAccess(item.minRole))
                  .map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={({ isActive }) =>
                        `group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                          isActive
                            ? "bg-gradient-to-r from-ot-blue/20 to-cyan-400/10 text-cyan-200 shadow-[0_0_0_1px_rgba(56,189,248,0.25)]"
                            : "text-slate-300 hover:bg-white/5 hover:text-white"
                        }`
                      }
                    >
                      <item.icon className="h-4 w-4 shrink-0" />
                      {!collapsed && <span className="truncate">{item.label}</span>}

                      {!collapsed && item.to === "/alerts" && unread > 0 ? (
                        <span className="ml-auto rounded-full bg-ot-red/90 px-2 py-0.5 text-[10px] font-semibold text-white">
                          {unread}
                        </span>
                      ) : null}
                    </NavLink>
                  ))}
              </div>
            </div>
          ))}
      </div>

      <div className="m-3 rounded-xl border border-cyan-300/20 bg-cyan-400/5 p-3">
        <div className="flex items-center gap-2 text-cyan-200">
          <ShieldCheck className="h-4 w-4" />
          {!collapsed && <span className="text-xs font-semibold uppercase tracking-wide">Session</span>}
        </div>
        {!collapsed && (
          <div className="mt-2 space-y-1 text-xs text-slate-300">
            <p>
              Role: <span className="font-medium text-white">{role || "viewer"}</span>
            </p>
            <p>
              Alerts: <span className="font-medium text-white">{unread}</span>
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}

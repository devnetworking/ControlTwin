import { NavLink } from "react-router-dom";
import { Bell, Cpu, LayoutDashboard, Network, Radio, Settings, Users } from "lucide-react";
import { useAlertStore } from "../../store/alertStore";
import { useAuth } from "../../hooks/useAuth";

const items = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/assets", label: "Assets", icon: Cpu },
  { to: "/topology", label: "Topology", icon: Network },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/collectors", label: "Collectors", icon: Radio, minRole: "ot_analyst" },
  { to: "/users", label: "Users", icon: Users, minRole: "admin" },
  { to: "/settings", label: "Settings", icon: Settings }
];

const ROLE_ORDER = ["viewer", "readonly", "ot_operator", "ot_analyst", "admin", "super_admin"];

export default function Sidebar({ collapsed, setCollapsed }) {
  const unread = useAlertStore((s) => s.unreadCount);
  const { role } = useAuth();

  return (
    <aside
      className={`border-r border-ot-border bg-[#081328] transition-all ${collapsed ? "w-16" : "w-56"} hidden md:block`}
    >
      <div className="flex h-14 items-center justify-between border-b border-ot-border px-3">
        {!collapsed && <span className="font-semibold text-ot-blue">ControlTwin</span>}
        <button onClick={() => setCollapsed((v) => !v)} className="rounded p-1 hover:bg-white/10">
          ≡
        </button>
      </div>
      <nav className="p-2">
        {items
          .filter((i) => !i.minRole || ROLE_ORDER.indexOf(role) >= ROLE_ORDER.indexOf(i.minRole))
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `mb-1 flex items-center gap-3 rounded px-3 py-2 text-sm ${
                  isActive ? "border-l-2 border-ot-blue bg-ot-blue/10 text-ot-blue" : "text-gray-300 hover:bg-white/5"
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              {!collapsed && <span>{item.label}</span>}
              {!collapsed && item.to === "/alerts" && unread > 0 ? (
                <span className="ml-auto rounded bg-ot-red px-1.5 text-xs text-white">{unread}</span>
              ) : null}
            </NavLink>
          ))}
      </nav>
    </aside>
  );
}

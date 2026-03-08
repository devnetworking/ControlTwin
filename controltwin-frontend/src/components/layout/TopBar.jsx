import { Bell, Search, Sparkles } from "lucide-react";
import { Avatar } from "../ui/avatar";
import { Badge } from "../ui/badge";
import { DropdownMenu, DropdownMenuItem } from "../ui/dropdown-menu";
import { useAlertStore } from "../../store/alertStore";
import { useAuth } from "../../hooks/useAuth";
import { useSiteContext } from "../../hooks/useSiteContext";
import { Select } from "../ui/select";
import { formatDate } from "../../lib/utils";

export default function TopBar({ sites = [] }) {
  const unread = useAlertStore((s) => s.unreadCount);
  const recentAlerts = useAlertStore((s) => s.recentAlerts);
  const markAllRead = useAlertStore((s) => s.markAllRead);
  const { user, logout } = useAuth();
  const { currentSite, setSite } = useSiteContext();

  const bellAlerts = (recentAlerts || []).slice(0, 5);

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-white/10 bg-[#0b1831]/85 px-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="w-56">
          <Select
            value={currentSite?.id || ""}
            onChange={(e) => {
              const site = sites.find((s) => String(s.id) === e.target.value) || null;
              setSite(site);
            }}
          >
            <option value="">All Sites</option>
            {sites.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </div>

        <div className="hidden items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 md:flex">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            placeholder="Quick search assets, alerts, users..."
            className="w-72 bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-500"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Badge className="hidden border border-cyan-400/30 bg-cyan-500/10 text-cyan-200 md:inline-flex">
          <Sparkles className="mr-1 h-3 w-3" />
          Admin Console
        </Badge>

        <DropdownMenu
          trigger={
            <button className="relative rounded-xl border border-white/10 bg-white/5 p-2 transition hover:bg-white/10">
              <Bell className="h-5 w-5 text-gray-200" />
              {unread > 0 && (
                <span className="absolute -right-1 -top-1 rounded-full bg-ot-red px-1.5 text-[10px] text-white">
                  {unread}
                </span>
              )}
            </button>
          }
        >
          {(close) => (
            <>
              <div className="min-w-[320px] p-2">
                <div className="mb-2 flex items-center justify-between px-2">
                  <div className="text-xs font-semibold uppercase tracking-wide text-gray-300">Recent Alerts</div>
                  <button
                    className="text-xs text-ot-blue hover:underline"
                    onClick={() => {
                      markAllRead();
                      close();
                    }}
                  >
                    Mark all read
                  </button>
                </div>

                {bellAlerts.length === 0 ? (
                  <div className="px-2 py-3 text-sm text-gray-300">No recent alerts</div>
                ) : (
                  <div className="space-y-1">
                    {bellAlerts.map((alert) => (
                      <div
                        key={alert.id}
                        className="rounded-md border border-white/10 bg-white/5 px-2 py-2 text-left"
                      >
                        <div className="text-xs uppercase tracking-wide text-ot-blue">
                          {alert.severity || "-"}
                        </div>
                        <div className="truncate text-sm text-white">{alert.title || "-"}</div>
                        <div className="text-xs text-gray-300">
                          Triggered at: {formatDate(alert.triggered_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </DropdownMenu>

        <DropdownMenu
          trigger={
            <div className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-2 py-1.5 hover:bg-white/10">
              <Avatar name={user?.full_name || user?.username || "User"} />
              <div className="hidden text-left md:block">
                <div className="text-sm text-white">{user?.username || "operator"}</div>
                <Badge variant="muted" className="mt-0.5">
                  {user?.role || "viewer"}
                </Badge>
              </div>
            </div>
          }
        >
          {(close) => (
            <>
              <DropdownMenuItem
                onClick={() => {
                  logout();
                  close();
                }}
              >
                Logout
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenu>
      </div>
    </header>
  );
}

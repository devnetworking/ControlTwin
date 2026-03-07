import { Bell } from "lucide-react";
import { Avatar } from "../ui/avatar";
import { Badge } from "../ui/badge";
import { DropdownMenu, DropdownMenuItem } from "../ui/dropdown-menu";
import { useAlertStore } from "../../store/alertStore";
import { useAuth } from "../../hooks/useAuth";
import { useSiteContext } from "../../hooks/useSiteContext";
import { Select } from "../ui/select";

export default function TopBar({ sites = [] }) {
  const unread = useAlertStore((s) => s.unreadCount);
  const { user, logout } = useAuth();
  const { currentSite, setSite } = useSiteContext();

  return (
    <header className="flex h-14 items-center justify-between border-b border-ot-border bg-ot-card px-4">
      <div className="w-64">
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

      <div className="flex items-center gap-4">
        <button className="relative rounded p-2 hover:bg-white/10">
          <Bell className="h-5 w-5 text-gray-200" />
          {unread > 0 && (
            <span className="absolute -right-0.5 -top-0.5 rounded-full bg-ot-red px-1.5 text-[10px] text-white">
              {unread}
            </span>
          )}
        </button>

        <DropdownMenu
          trigger={
            <div className="flex items-center gap-2">
              <Avatar name={user?.full_name || user?.username || "User"} />
              <div className="hidden text-left md:block">
                <div className="text-sm">{user?.username || "operator"}</div>
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

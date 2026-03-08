import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import { getSites } from "../../api/sites";

export default function AppLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const { data } = useQuery({
    queryKey: ["sites"],
    queryFn: getSites,
    staleTime: 60000
  });

  const sites = data?.items || data || [];

  return (
    <div className="flex h-screen bg-[radial-gradient(circle_at_top,#102448_0%,#060c1a_45%,#030712_100%)] text-white">
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar sites={sites} />
        <main className="min-h-0 flex-1 overflow-auto p-4 md:p-6">
          <div className="mx-auto w-full rounded-2xl border border-white/10 bg-[#0b1428]/60 p-4 shadow-[0_10px_40px_rgba(2,12,27,0.4)] backdrop-blur md:p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

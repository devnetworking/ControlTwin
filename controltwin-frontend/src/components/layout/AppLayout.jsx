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
    <div className="flex h-screen bg-ot-bg text-white">
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar sites={sites} />
        <main className="min-h-0 flex-1 overflow-auto p-4">{children}</main>
      </div>
    </div>
  );
}

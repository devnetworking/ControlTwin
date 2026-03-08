import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Eye, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAssets, useCreateAsset } from "../hooks/useAssets";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Select } from "../components/ui/select";
import { Dialog } from "../components/ui/dialog";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import StatusDot from "../components/ui/StatusDot";
import EmptyState from "../components/ui/EmptyState";
import { ASSET_TYPES, STATUS_OPTIONS } from "../constants/ics";
import { getSites } from "../api/sites";
import { formatDate } from "../lib/utils";
import { useLang } from "../lang";

const PAGE_SIZE = 20;

export default function AssetsPage() {
  const { t } = useLang();
  const navigate = useNavigate();
  const [filters, setFilters] = useState({ q: "", asset_type: "", status: "", criticality: "" });
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(false);
  const [newAsset, setNewAsset] = useState({ tag: "", name: "", asset_type: "plc", protocol: "modbus_tcp", site_id: "" });
  const [errorMessage, setErrorMessage] = useState("");

  const { data } = useAssets(filters);
  const createAsset = useCreateAsset();
  const [sites, setSites] = useState([]);

  const assets = data?.items || data || [];
  const filtered = useMemo(() => {
    let v = assets;
    if (filters.q) {
      const q = filters.q.toLowerCase();
      v = v.filter((a) => (a.name || "").toLowerCase().includes(q) || (a.tag || "").toLowerCase().includes(q));
    }
    if (filters.asset_type) v = v.filter((a) => a.asset_type === filters.asset_type);
    if (filters.status) v = v.filter((a) => a.status === filters.status);
    if (filters.criticality) v = v.filter((a) => String(a.criticality || "") === filters.criticality);
    return v;
  }, [assets, filters]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  useEffect(() => {
    (async () => {
      try {
        const s = await getSites();
        setSites(s?.items || s || []);
      } catch {
        setSites([]);
      }
    })();
  }, []);

  async function submitCreate(e) {
    e.preventDefault();
    if (!newAsset.tag || !newAsset.name || !newAsset.asset_type || !newAsset.site_id || !newAsset.protocol) return;
    setErrorMessage("");

    try {
      await createAsset.mutateAsync(newAsset);
      setOpen(false);
      setNewAsset({ tag: "", name: "", asset_type: "plc", protocol: "modbus_tcp", site_id: "" });
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 422) {
        setErrorMessage("Invalid asset data. Please check required fields and formats.");
      } else {
        setErrorMessage("Failed to create asset. Please try again.");
      }
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t("assets.title")}</h1>
        <Button onClick={() => navigate("/assets/new")}>
          <Plus className="mr-2 h-4 w-4" /> {t("assets.addAsset")}
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Input
          placeholder={t("assets.search")}
          value={filters.q}
          onChange={(e) => {
            setFilters((s) => ({ ...s, q: e.target.value }));
            setPage(1);
          }}
        />
        <Select
          value={filters.asset_type}
          onChange={(e) => {
            setFilters((s) => ({ ...s, asset_type: e.target.value }));
            setPage(1);
          }}
        >
          <option value="">{t("alerts.all")} {t("assets.type")}</option>
          {ASSET_TYPES.map((t, idx) => (
            <option key={`filter-asset-type-${t.value || "unknown"}-${idx}`} value={t.value}>{t.label}</option>
          ))}
        </Select>
        <Select
          value={filters.status}
          onChange={(e) => {
            setFilters((s) => ({ ...s, status: e.target.value }));
            setPage(1);
          }}
        >
          <option value="">{t("alerts.all")} {t("assets.status")}</option>
          {STATUS_OPTIONS.map((s, idx) => {
            const value = typeof s === "string" ? s : s.value;
            const label = typeof s === "string" ? s : s.label;
            return (
              <option key={`status-${value || "unknown"}-${idx}`} value={value}>
                {label}
              </option>
            );
          })}
        </Select>
        <Input
          placeholder="Criticality"
          value={filters.criticality}
          onChange={(e) => {
            setFilters((s) => ({ ...s, criticality: e.target.value }));
            setPage(1);
          }}
        />
      </div>

      <div className="text-sm text-gray-300">{filtered.length} assets</div>

      {!filtered.length ? (
        <EmptyState title={t("assets.noAssets")} description={t("common.retry")} />
      ) : (
        <div className="rounded-lg border border-ot-border bg-ot-card">
          <Table>
            <THead>
              <TR>
                <TH>Tag</TH>
                <TH>{t("assets.name")}</TH>
                <TH>{t("assets.type")}</TH>
                <TH>{t("assets.protocol")}</TH>
                <TH>{t("assets.ipAddress")}</TH>
                <TH>Purdue</TH>
                <TH>{t("assets.status")}</TH>
                <TH>{t("assets.lastSeen")}</TH>
                <TH>{t("assets.actions")}</TH>
              </TR>
            </THead>
            <TBody>
              {pageItems.map((a) => (
                <TR key={a.id}>
                  <TD className="font-mono">{a.tag}</TD>
                  <TD>{a.name}</TD>
                  <TD>{a.asset_type}</TD>
                  <TD>{a.protocol || "-"}</TD>
                  <TD>{a.ip_address || "-"}</TD>
                  <TD>{a.purdue_level ?? "-"}</TD>
                  <TD><StatusDot status={a.status || "offline"} /></TD>
                  <TD>{formatDate(a.last_seen)}</TD>
                  <TD>
                    <Button size="sm" variant="ghost" onClick={() => navigate(`/assets/${a.id}`)}>
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      )}

      <div className="flex items-center justify-end gap-2">
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Prev
        </Button>
        <span className="text-sm text-gray-300">
          {page}/{totalPages}
        </span>
        <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
          Next
        </Button>
      </div>

      <Dialog open={open} onOpenChange={setOpen} title="Register Asset">
        <form className="space-y-3" onSubmit={submitCreate}>
          <Input
            placeholder="Tag"
            value={newAsset.tag}
            onChange={(e) => setNewAsset((s) => ({ ...s, tag: e.target.value }))}
            required
          />
          <Input
            placeholder="Name"
            value={newAsset.name}
            onChange={(e) => setNewAsset((s) => ({ ...s, name: e.target.value }))}
            required
          />
          <Select
            value={newAsset.asset_type}
            onChange={(e) => setNewAsset((s) => ({ ...s, asset_type: e.target.value }))}
          >
            {ASSET_TYPES.map((t, idx) => (
              <option key={`create-asset-type-${t.value || "unknown"}-${idx}`} value={t.value}>{t.label}</option>
            ))}
          </Select>
          <Select
            value={newAsset.protocol}
            onChange={(e) => setNewAsset((s) => ({ ...s, protocol: e.target.value }))}
          >
            <option value="modbus_tcp">modbus_tcp</option>
            <option value="opcua">opcua</option>
            <option value="mqtt">mqtt</option>
            <option value="http">http</option>
            <option value="simulated">simulated</option>
          </Select>
          <Select
            value={newAsset.site_id}
            onChange={(e) => setNewAsset((s) => ({ ...s, site_id: e.target.value }))}
          >
            <option value="">Select Site</option>
            {sites.map((site, idx) => (
              <option key={`create-site-${site.id || idx}`} value={site.id}>
                {site.name || site.id}
              </option>
            ))}
          </Select>
          {errorMessage ? <p className="text-sm text-ot-red">{errorMessage}</p> : null}
          <Button type="submit" className="w-full" disabled={createAsset.isPending}>
            {createAsset.isPending ? "Creating..." : "Create Asset"}
          </Button>
        </form>
      </Dialog>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useCreateAsset } from "../hooks/useAssets";
import { getSites } from "../api/sites";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import { ASSET_TYPES } from "../constants/ics";

const INITIAL_ASSET = {
  tag: "",
  name: "",
  asset_type: "plc",
  protocol: "modbus_tcp",
  site_id: "",
  ip_address: "",
  port: "",
  purdue_level: "0"
};

export default function AssetCreatePage() {
  const navigate = useNavigate();
  const createAsset = useCreateAsset();

  const [sites, setSites] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [newAsset, setNewAsset] = useState(INITIAL_ASSET);

  const protocolOptions = useMemo(
    () =>
      new Set([
        "modbus_tcp",
        "modbus_rtu",
        "opcua",
        "dnp3",
        "iec61850",
        "iccp",
        "ethernetip",
        "profinet",
        "bacnet",
        "mqtt",
        "other"
      ]),
    []
  );

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

    const normalizedProtocol = String(newAsset.protocol).trim().toLowerCase();
    if (!protocolOptions.has(normalizedProtocol)) {
      setErrorMessage("Invalid protocol value.");
      return;
    }

    const payload = {
      ...newAsset,
      tag: newAsset.tag.trim(),
      name: newAsset.name.trim(),
      site_id: String(newAsset.site_id).trim(),
      protocol: normalizedProtocol,
      asset_type: String(newAsset.asset_type).trim(),
      purdue_level: newAsset.purdue_level !== "" ? Number(newAsset.purdue_level) : 0,
      port: newAsset.port !== "" ? Number(newAsset.port) : undefined,
      ip_address: newAsset.ip_address?.trim() ? newAsset.ip_address.trim() : undefined
    };

    try {
      await createAsset.mutateAsync(payload);
      navigate("/assets");
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === "string" && detail.trim()) {
          setErrorMessage(detail);
          return;
        }
        if (Array.isArray(detail) && detail.length > 0) {
          const first = detail[0];
          if (first?.msg) {
            setErrorMessage(first.msg);
            return;
          }
        }
        if (error.response?.status === 422) {
          setErrorMessage("Invalid asset data. Please check required fields and formats.");
          return;
        }
      }
      setErrorMessage("Failed to create asset. Please try again.");
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Ajouter un équipement</h1>
        <Button variant="outline" onClick={() => navigate("/assets")}>
          Retour aux assets
        </Button>
      </div>

      <div className="rounded-lg border border-ot-border bg-ot-card p-4">
        <form className="space-y-3" onSubmit={submitCreate}>
          <Input
            placeholder="Tag (ex: RX-03)"
            value={newAsset.tag}
            onChange={(e) => setNewAsset((s) => ({ ...s, tag: e.target.value }))}
            required
          />
          <Input
            placeholder="Nom (ex: PLC Controller RX-03)"
            value={newAsset.name}
            onChange={(e) => setNewAsset((s) => ({ ...s, name: e.target.value }))}
            required
          />
          <Select
            value={newAsset.asset_type}
            onChange={(e) => setNewAsset((s) => ({ ...s, asset_type: e.target.value }))}
          >
            {ASSET_TYPES.map((t, idx) => (
              <option key={`create-page-asset-type-${t.value || "unknown"}-${idx}`} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
          <Select
            value={newAsset.protocol}
            onChange={(e) => setNewAsset((s) => ({ ...s, protocol: e.target.value }))}
          >
            <option value="modbus_tcp">modbus_tcp</option>
            <option value="modbus_rtu">modbus_rtu</option>
            <option value="opcua">opcua</option>
            <option value="dnp3">dnp3</option>
            <option value="iec61850">iec61850</option>
            <option value="iccp">iccp</option>
            <option value="ethernetip">ethernetip</option>
            <option value="profinet">profinet</option>
            <option value="bacnet">bacnet</option>
            <option value="mqtt">mqtt</option>
            <option value="other">other</option>
          </Select>
          <Input
            placeholder="IP Address (optionnel)"
            value={newAsset.ip_address}
            onChange={(e) => setNewAsset((s) => ({ ...s, ip_address: e.target.value }))}
          />
          <Input
            placeholder="Port (optionnel)"
            type="number"
            value={newAsset.port}
            onChange={(e) => setNewAsset((s) => ({ ...s, port: e.target.value }))}
          />
          <Input
            placeholder="Purdue Level (0-4)"
            type="number"
            min="0"
            max="4"
            value={newAsset.purdue_level}
            onChange={(e) => setNewAsset((s) => ({ ...s, purdue_level: e.target.value }))}
            required
          />
          <Select
            value={newAsset.site_id}
            onChange={(e) => setNewAsset((s) => ({ ...s, site_id: e.target.value }))}
          >
            <option value="">Sélectionner un site</option>
            {sites.map((site, idx) => (
              <option key={`create-page-site-${site.id || idx}`} value={site.id}>
                {site.name || site.id}
              </option>
            ))}
          </Select>

          {errorMessage ? <p className="text-sm text-ot-red">{errorMessage}</p> : null}

          <Button type="submit" className="w-full" disabled={createAsset.isPending}>
            {createAsset.isPending ? "Création..." : "Créer l’équipement"}
          </Button>
        </form>
      </div>
    </div>
  );
}

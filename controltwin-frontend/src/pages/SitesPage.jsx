import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Pencil, Plus, Power, RefreshCw, Trash2, X } from "lucide-react";
import {
  activateSite,
  createSite,
  deactivateSite,
  deleteSite,
  getSites,
  updateSite
} from "../api/sites";

const defaultForm = {
  name: "",
  description: ""
};

export default function SitesPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [editingSiteId, setEditingSiteId] = useState(null);
  const [editForm, setEditForm] = useState(defaultForm);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["sites"],
    queryFn: getSites,
    staleTime: 30000
  });

  const sites = useMemo(() => data?.items || data || [], [data]);

  const createMutation = useMutation({
    mutationFn: createSite,
    onSuccess: () => {
      setName("");
      setDescription("");
      queryClient.invalidateQueries({ queryKey: ["sites"] });
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }) => updateSite(id, payload),
    onSuccess: () => {
      setEditingSiteId(null);
      setEditForm(defaultForm);
      queryClient.invalidateQueries({ queryKey: ["sites"] });
    }
  });

  const activateMutation = useMutation({
    mutationFn: activateSite,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sites"] })
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateSite,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sites"] })
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSite,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sites"] })
  });

  const onSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    createMutation.mutate({
      name: name.trim(),
      description: description.trim() || null
    });
  };

  const startEdit = (site) => {
    setEditingSiteId(site.id);
    setEditForm({
      name: site.name || "",
      description: site.description || ""
    });
  };

  const cancelEdit = () => {
    setEditingSiteId(null);
    setEditForm(defaultForm);
  };

  const submitEdit = (siteId) => {
    if (!editForm.name.trim()) return;
    updateMutation.mutate({
      id: siteId,
      payload: {
        name: editForm.name.trim(),
        description: editForm.description.trim() || null
      }
    });
  };

  const toggleActive = (site) => {
    if (site.is_active) {
      deactivateMutation.mutate(site.id);
    } else {
      activateMutation.mutate(site.id);
    }
  };

  const handleDelete = (site) => {
    const ok = window.confirm(`Supprimer (désactiver) le site "${site.name}" ?`);
    if (!ok) return;
    deleteMutation.mutate(site.id);
  };

  return (
    <div className="space-y-6">
      <header className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-cyan-300/30 bg-cyan-400/10 p-2">
            <Building2 className="h-5 w-5 text-cyan-200" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white">Site Management</h1>
            <p className="text-sm text-slate-300">Créer et gérer les sites industriels.</p>
          </div>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-3">
        <form
          onSubmit={onSubmit}
          className="rounded-2xl border border-white/10 bg-[#0B1730]/70 p-5 lg:col-span-1"
        >
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-300">
            Ajouter un site
          </h2>

          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-slate-300">Nom du site</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Plant North"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none ring-cyan-400/40 placeholder:text-slate-400 focus:ring"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-300">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                placeholder="Description du site..."
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none ring-cyan-400/40 placeholder:text-slate-400 focus:ring"
              />
            </div>

            {createMutation.isError ? (
              <p className="text-xs text-red-300">
                {(createMutation.error && createMutation.error.message) ||
                  "Erreur lors de la création du site."}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={createMutation.isPending || !name.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-4 py-2 text-sm font-medium text-[#001226] transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Plus className="h-4 w-4" />
              {createMutation.isPending ? "Création..." : "Créer le site"}
            </button>
          </div>
        </form>

        <div className="rounded-2xl border border-white/10 bg-[#0B1730]/70 p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
              Sites existants
            </h2>
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-200 transition hover:bg-white/10"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>

          {isLoading ? (
            <p className="text-sm text-slate-300">Chargement des sites...</p>
          ) : isError ? (
            <p className="text-sm text-red-300">
              {(error && error.message) || "Impossible de charger les sites."}
            </p>
          ) : sites.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/20 bg-white/[0.03] p-6 text-center text-sm text-slate-300">
              Aucun site trouvé. Créez votre premier site avec le formulaire à gauche.
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-white/10">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead className="bg-white/[0.03]">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-slate-300">Nom</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-300">Description</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-300">État</th>
                    <th className="px-4 py-3 text-right font-medium text-slate-300">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {sites.map((site, idx) => {
                    const isEditing = editingSiteId === site.id;
                    return (
                      <tr key={site.id || idx} className="hover:bg-white/[0.03]">
                        <td className="px-4 py-3 text-white">
                          {isEditing ? (
                            <input
                              value={editForm.name}
                              onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))}
                              className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-sm text-white outline-none ring-cyan-400/40 focus:ring"
                            />
                          ) : (
                            site.name || "-"
                          )}
                        </td>
                        <td className="px-4 py-3 text-slate-300">
                          {isEditing ? (
                            <input
                              value={editForm.description}
                              onChange={(e) =>
                                setEditForm((prev) => ({ ...prev, description: e.target.value }))
                              }
                              className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-sm text-white outline-none ring-cyan-400/40 focus:ring"
                            />
                          ) : (
                            site.description || "-"
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex rounded-full px-2 py-1 text-xs ${
                              site.is_active
                                ? "bg-emerald-500/20 text-emerald-200"
                                : "bg-slate-500/20 text-slate-300"
                            }`}
                          >
                            {site.is_active ? "Actif" : "Inactif"}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-2">
                            {isEditing ? (
                              <>
                                <button
                                  onClick={() => submitEdit(site.id)}
                                  disabled={updateMutation.isPending || !editForm.name.trim()}
                                  className="inline-flex items-center gap-1 rounded-lg bg-cyan-500 px-2.5 py-1.5 text-xs font-medium text-[#001226] hover:bg-cyan-400 disabled:opacity-60"
                                >
                                  <Pencil className="h-3.5 w-3.5" />
                                  Save
                                </button>
                                <button
                                  onClick={cancelEdit}
                                  className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-slate-200 hover:bg-white/10"
                                >
                                  <X className="h-3.5 w-3.5" />
                                  Cancel
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  onClick={() => startEdit(site)}
                                  className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-slate-200 hover:bg-white/10"
                                >
                                  <Pencil className="h-3.5 w-3.5" />
                                  Modifier
                                </button>
                                <button
                                  onClick={() => toggleActive(site)}
                                  disabled={activateMutation.isPending || deactivateMutation.isPending}
                                  className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-slate-200 hover:bg-white/10 disabled:opacity-60"
                                >
                                  <Power className="h-3.5 w-3.5" />
                                  {site.is_active ? "Désactiver" : "Activer"}
                                </button>
                                <button
                                  onClick={() => handleDelete(site)}
                                  disabled={deleteMutation.isPending}
                                  className="inline-flex items-center gap-1 rounded-lg border border-red-400/30 bg-red-500/10 px-2.5 py-1.5 text-xs text-red-200 hover:bg-red-500/20 disabled:opacity-60"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                  Supprimer
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

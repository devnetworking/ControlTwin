import { useEffect } from "react";
import { create } from "zustand";
import { getSites } from "../api/sites";

const SITE_STORAGE_KEY = "controltwin.currentSiteId";

const useSiteStore = create((set, get) => ({
  currentSite: null,
  currentSiteId: null,
  sites: [],
  isLoading: false,

  setCurrentSite: (site) =>
    set(() => ({
      currentSite: site || null,
      currentSiteId: site?.id || null,
    })),

  setSite: (site) =>
    set(() => {
      const siteId = site?.id || null;
      if (siteId) {
        localStorage.setItem(SITE_STORAGE_KEY, String(siteId));
      } else {
        localStorage.removeItem(SITE_STORAGE_KEY);
      }
      return {
        currentSite: site || null,
        currentSiteId: siteId,
      };
    }),

  loadSites: async () => {
    set({ isLoading: true });
    try {
      const data = await getSites();
      const sites = Array.isArray(data) ? data : data?.items || [];
      const savedId = localStorage.getItem(SITE_STORAGE_KEY);
      const selected = (savedId && sites.find((s) => String(s?.id) === String(savedId))) || sites[0] || null;

      if (selected?.id) {
        localStorage.setItem(SITE_STORAGE_KEY, String(selected.id));
      }

      set({
        sites,
        currentSite: selected,
        currentSiteId: selected?.id || null,
        isLoading: false,
      });
    } catch {
      const state = get();
      set({
        sites: state.sites || [],
        isLoading: false,
      });
    }
  },
}));

export function useSiteContext() {
  const currentSite = useSiteStore((s) => s.currentSite);
  const currentSiteId = useSiteStore((s) => s.currentSiteId);
  const sites = useSiteStore((s) => s.sites);
  const isLoading = useSiteStore((s) => s.isLoading);
  const setCurrentSite = useSiteStore((s) => s.setCurrentSite);
  const setSite = useSiteStore((s) => s.setSite);
  const loadSites = useSiteStore((s) => s.loadSites);

  useEffect(() => {
    loadSites();
  }, [loadSites]);

  return {
    currentSite,
    currentSiteId,
    setCurrentSite,
    sites,
    isLoading,
    setSite,
  };
}

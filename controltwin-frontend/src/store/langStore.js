import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

const useLangStore = create(
  persist(
    (set) => ({
      lang: "fr",
      setLang: (lang) => set({ lang }),
    }),
    {
      name: "controltwin_lang",
      storage: createJSONStorage(() => localStorage),
    }
  )
);

export default useLangStore;

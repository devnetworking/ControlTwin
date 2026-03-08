import { useState } from "react";
import { useLang } from "../lang";
import useLangStore from "../store/langStore";

export default function SettingsPage() {
  const { t, lang } = useLang();
  const setLang = useLangStore((s) => s.setLang);
  const [darkMode] = useState(true);

  return (
    <div className="space-y-6 bg-[#0A1628] text-white">
      <div className="rounded-lg border border-[#1B3A6B] bg-[#0F1F3D] p-6">
        <h1 className="text-2xl font-semibold">{t("settings.title")}</h1>
      </div>

      <section className="rounded-lg border border-[#1B3A6B] bg-[#0F1F3D] p-6 space-y-4">
        <h2 className="text-lg font-semibold">Langue / Language</h2>
        <p className="text-sm text-slate-300">{t("settings.selectLanguage")}</p>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setLang("fr")}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              lang === "fr"
                ? "border border-[#00A8E8] bg-[#00A8E8] text-white"
                : "border border-[#1B3A6B] bg-[#0A1628] text-slate-200 hover:border-[#00A8E8]"
            }`}
          >
            Français
          </button>

          <button
            type="button"
            onClick={() => setLang("en")}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              lang === "en"
                ? "border border-[#00A8E8] bg-[#00A8E8] text-white"
                : "border border-[#1B3A6B] bg-[#0A1628] text-slate-200 hover:border-[#00A8E8]"
            }`}
          >
            English
          </button>
        </div>
      </section>

      <section className="rounded-lg border border-[#1B3A6B] bg-[#0F1F3D] p-6 space-y-4">
        <h2 className="text-lg font-semibold">{t("settings.theme")}</h2>
        <div className="flex items-center justify-between rounded-lg border border-[#1B3A6B] bg-[#0A1628] px-4 py-3">
          <span className="text-sm text-slate-200">{t("settings.darkMode")}</span>
          <button
            type="button"
            className={`h-6 w-12 rounded-full transition ${darkMode ? "bg-[#00A8E8]" : "bg-slate-600"}`}
            aria-label={t("settings.darkMode")}
          >
            <span
              className={`block h-6 w-6 rounded-full bg-white transition ${
                darkMode ? "translate-x-6" : "translate-x-0"
              }`}
            />
          </button>
        </div>
      </section>
    </div>
  );
}

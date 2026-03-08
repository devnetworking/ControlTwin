import fr from "./fr";
import en from "./en";
import useLangStore from "../store/langStore";

const translations = { fr, en };

export function useLang() {
  const lang = useLangStore((s) => s.lang);
  const dict = translations[lang] || translations.fr;

  function t(key) {
    return key.split(".").reduce((obj, k) => obj?.[k], dict) ?? key;
  }

  return { t, lang };
}

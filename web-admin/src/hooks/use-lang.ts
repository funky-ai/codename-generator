import { useState, useCallback } from "react";
import { getLang, toggleLang, t, type Lang, type TranslationKey } from "@/lib/i18n";

export function useLang() {
  const [lang, setLangState] = useState<Lang>(getLang);

  const toggle = useCallback(() => {
    const next = toggleLang();
    setLangState(next);
  }, []);

  const translate = useCallback(
    (key: TranslationKey) => t(key),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lang]
  );

  return { lang, toggle, t: translate };
}

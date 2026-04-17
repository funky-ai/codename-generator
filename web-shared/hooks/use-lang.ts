import { useState, useCallback } from "react";
import type { I18n, Lang } from "../lib/i18n-base";

export function createUseLang<TKey extends string>(i18n: I18n<TKey>) {
  return function useLang() {
    const [lang, setLangState] = useState<Lang>(i18n.getLang);

    const toggle = useCallback(() => {
      const next = i18n.toggleLang();
      setLangState(next);
    }, []);

    const translate = useCallback(
      (key: TKey) => i18n.t(key),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [lang]
    );

    return { lang, toggle, t: translate };
  };
}

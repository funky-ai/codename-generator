import {
  baseTranslations,
  createI18n,
  type Lang,
} from "@shared/lib/i18n-base";
import { createUseLang } from "@shared/hooks/use-lang";

// End-user-facing extras: friendly labels for the public client. The admin
// client has its own extras (Add / Edit / Logs / Assign etc.) that are not
// relevant here — the user client is read-only.
const userExtras = {
  zh: {
    home: "首页",
    browse: "浏览",
    getStarted: "开始使用",
    pickOne: "抽一个代号",
    browseAll: "浏览代号库",
    availableNow: "当前可用",
    totalLibrary: "代号总数",
    allAssigned: "已分配",
    emptyHint: "暂无代号可浏览。请联系管理员补充。",
    noMatches: "没有匹配的代号",
    suggestionsReady: "已为你抽出以下代号",
    tryAgain: "再抽一次",
  },
  en: {
    home: "Home",
    browse: "Browse",
    getStarted: "Get Started",
    pickOne: "Pick a Codename",
    browseAll: "Browse Library",
    availableNow: "Available Now",
    totalLibrary: "Total Codenames",
    allAssigned: "Assigned",
    emptyHint: "No codenames to browse yet. Please contact an administrator.",
    noMatches: "No matching codenames",
    suggestionsReady: "Here are your random codenames",
    tryAgain: "Try Again",
  },
} as const;

const translations = {
  zh: { ...baseTranslations.zh, ...userExtras.zh },
  en: { ...baseTranslations.en, ...userExtras.en },
} as const;

export type TranslationKey = keyof (typeof translations)["zh"];
export type { Lang };

const i18n = createI18n<TranslationKey>(translations);
export const { getLang, setLang, t, toggleLang } = i18n;
export const useLang = createUseLang<TranslationKey>(i18n);

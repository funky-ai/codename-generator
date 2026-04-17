export const baseTranslations = {
  zh: {
    appName: "代号生成器",
    dashboard: "仪表盘",
    inventory: "代号库",
    draw: "随机抽取",
    assignments: "分配记录",
    total: "总计",
    available: "可用",
    assigned: "已分配",
    person: "人物",
    animal: "动物",
    theme: "主题",
    subTheme: "子主题",
    status: "状态",
    name: "名称",
    nameEn: "英文名",
    nameZh: "中文名",
    brief: "简介",
    search: "搜索",
    filter: "筛选",
    all: "全部",
    count: "数量",
    drawRandom: "随机抽取",
    description: "描述",
    assignedBy: "分配人",
    timestamp: "时间",
    lowStockWarning: "库存不足警告",
    noData: "暂无数据",
    loading: "加载中...",
    error: "错误",
    quickActions: "快捷操作",
    themeBreakdown: "主题分布",
    recentLogs: "最近操作",
    codenames: "代号",
    byTheme: "按主题",
    language: "English",
  },
  en: {
    appName: "Codename Generator",
    dashboard: "Dashboard",
    inventory: "Inventory",
    draw: "Draw Random",
    assignments: "Assignments",
    total: "Total",
    available: "Available",
    assigned: "Assigned",
    person: "Person",
    animal: "Animal",
    theme: "Theme",
    subTheme: "Sub-theme",
    status: "Status",
    name: "Name",
    nameEn: "English Name",
    nameZh: "Chinese Name",
    brief: "Brief",
    search: "Search",
    filter: "Filter",
    all: "All",
    count: "Count",
    drawRandom: "Draw Random",
    description: "Description",
    assignedBy: "Assigned By",
    timestamp: "Timestamp",
    lowStockWarning: "Low Stock Warning",
    noData: "No data",
    loading: "Loading...",
    error: "Error",
    quickActions: "Quick Actions",
    themeBreakdown: "Theme Breakdown",
    recentLogs: "Recent Activity",
    codenames: "Codenames",
    byTheme: "By Theme",
    language: "中文",
  },
} as const;

export type Lang = keyof typeof baseTranslations;
export type BaseTranslationKey = keyof (typeof baseTranslations)["zh"];

export interface I18n<TKey extends string> {
  getLang: () => Lang;
  setLang: (lang: Lang) => void;
  t: (key: TKey) => string;
  toggleLang: () => Lang;
}

export function createI18n<TKey extends string>(
  translations: Record<Lang, Record<TKey, string>>,
  storageKey = "lang"
): I18n<TKey> {
  const hasStorage = typeof localStorage !== "undefined";
  let currentLang: Lang =
    (hasStorage && (localStorage.getItem(storageKey) as Lang)) || "zh";

  return {
    getLang: () => currentLang,
    setLang: (lang: Lang) => {
      currentLang = lang;
      if (hasStorage) localStorage.setItem(storageKey, lang);
    },
    t: (key: TKey) => translations[currentLang][key],
    toggleLang: () => {
      const next: Lang = currentLang === "zh" ? "en" : "zh";
      currentLang = next;
      if (hasStorage) localStorage.setItem(storageKey, next);
      return next;
    },
  };
}

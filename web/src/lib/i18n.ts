const translations = {
  zh: {
    appName: "代号生成器",
    dashboard: "仪表盘",
    inventory: "代号库",
    add: "添加代号",
    draw: "随机抽取",
    assignments: "分配记录",
    logs: "操作日志",
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
    addMore: "再添加一条",
    submit: "提交",
    cancel: "取消",
    confirm: "确认",
    edit: "编辑",
    assign: "分配",
    drawRandom: "随机抽取",
    count: "数量",
    operator: "操作人",
    description: "描述",
    assignedBy: "分配人",
    timestamp: "时间",
    action: "操作",
    details: "详情",
    added: "添加",
    updated: "更新",
    lowStockWarning: "库存不足警告",
    noData: "暂无数据",
    assignConfirm: "确认分配此代号？此操作不可逆！",
    assignSuccess: "分配成功",
    addSuccess: "添加成功",
    updateSuccess: "更新成功",
    error: "错误",
    loading: "加载中...",
    quickActions: "快捷操作",
    themeBreakdown: "主题分布",
    recentLogs: "最近操作",
    personRequired: "人物主题必须选择子主题",
    codenames: "代号",
    byTheme: "按主题",
    language: "English",
  },
  en: {
    appName: "Codename Generator",
    dashboard: "Dashboard",
    inventory: "Inventory",
    add: "Add Codenames",
    draw: "Draw Random",
    assignments: "Assignments",
    logs: "Logs",
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
    addMore: "Add Another",
    submit: "Submit",
    cancel: "Cancel",
    confirm: "Confirm",
    edit: "Edit",
    assign: "Assign",
    drawRandom: "Draw Random",
    count: "Count",
    operator: "Operator",
    description: "Description",
    assignedBy: "Assigned By",
    timestamp: "Timestamp",
    action: "Action",
    details: "Details",
    added: "Added",
    updated: "Updated",
    lowStockWarning: "Low Stock Warning",
    noData: "No data",
    assignConfirm: "Confirm assigning this codename? This action is IRREVERSIBLE!",
    assignSuccess: "Assignment successful",
    addSuccess: "Added successfully",
    updateSuccess: "Updated successfully",
    error: "Error",
    loading: "Loading...",
    quickActions: "Quick Actions",
    themeBreakdown: "Theme Breakdown",
    recentLogs: "Recent Activity",
    personRequired: "Person theme requires a sub-theme",
    codenames: "Codenames",
    byTheme: "By Theme",
    language: "中文",
  },
} as const;

export type Lang = keyof typeof translations;
export type TranslationKey = keyof (typeof translations)["zh"];

let currentLang: Lang =
  (localStorage.getItem("lang") as Lang) || "zh";

export function getLang(): Lang {
  return currentLang;
}

export function setLang(lang: Lang): void {
  currentLang = lang;
  localStorage.setItem("lang", lang);
}

export function t(key: TranslationKey): string {
  return translations[currentLang][key];
}

export function toggleLang(): Lang {
  const next = currentLang === "zh" ? "en" : "zh";
  setLang(next);
  return next;
}

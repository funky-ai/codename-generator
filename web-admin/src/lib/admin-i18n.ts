import {
  baseTranslations,
  createI18n,
  type Lang,
} from "@shared/lib/i18n-base";
import { createUseLang } from "@shared/hooks/use-lang";

const adminExtras = {
  zh: {
    add: "添加代号",
    logs: "操作日志",
    addMore: "再添加一条",
    submit: "提交",
    cancel: "取消",
    confirm: "确认",
    edit: "编辑",
    assign: "分配",
    operator: "操作人",
    action: "操作",
    details: "详情",
    added: "添加",
    updated: "更新",
    assignConfirm: "确认分配此代号？此操作不可逆！",
    assignSuccess: "分配成功",
    addSuccess: "添加成功",
    updateSuccess: "更新成功",
    personRequired: "人物主题必须选择子主题",
  },
  en: {
    add: "Add Codenames",
    logs: "Logs",
    addMore: "Add Another",
    submit: "Submit",
    cancel: "Cancel",
    confirm: "Confirm",
    edit: "Edit",
    assign: "Assign",
    operator: "Operator",
    action: "Action",
    details: "Details",
    added: "Added",
    updated: "Updated",
    assignConfirm: "Confirm assigning this codename? This action is IRREVERSIBLE!",
    assignSuccess: "Assignment successful",
    addSuccess: "Added successfully",
    updateSuccess: "Updated successfully",
    personRequired: "Person theme requires a sub-theme",
  },
} as const;

const translations = {
  zh: { ...baseTranslations.zh, ...adminExtras.zh },
  en: { ...baseTranslations.en, ...adminExtras.en },
} as const;

export type TranslationKey = keyof (typeof translations)["zh"];
export type { Lang };

const i18n = createI18n<TranslationKey>(translations);
export const { getLang, setLang, t, toggleLang } = i18n;
export const useLang = createUseLang<TranslationKey>(i18n);

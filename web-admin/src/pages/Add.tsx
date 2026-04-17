import { useCallback, useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@shared/components/ui/card";
import { Button } from "@shared/components/ui/button";
import { Input } from "@shared/components/ui/input";
import { Label } from "@shared/components/ui/label";
import { Textarea } from "@shared/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@shared/components/ui/select";
import { Plus, Send, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, type Category, type CodenameInput } from "@shared/lib/api";
import { useLang } from "@/lib/admin-i18n";

interface FormRow {
  key: number;
  name: string;
  name_en: string;
  name_zh: string;
  category_id: string;
  brief: string;
}

let nextKey = 1;
function emptyRow(): FormRow {
  return {
    key: nextKey++,
    name: "",
    name_en: "",
    name_zh: "",
    category_id: "",
    brief: "",
  };
}

interface LeafOption {
  category_id: string;
  label: string; // "person > science"
}

function collectLeaves(tree: Category[], lang: "zh" | "en"): LeafOption[] {
  const out: LeafOption[] = [];
  const walk = (node: Category, path: string[]) => {
    const displayName = lang === "zh" ? node.name_zh : node.name_en;
    const nextPath = [...path, displayName];
    if (!node.children || node.children.length === 0) {
      if (!node.is_archived) {
        out.push({
          category_id: node.category_id,
          label: nextPath.join(" › "),
        });
      }
      return;
    }
    for (const child of node.children) walk(child, nextPath);
  };
  for (const root of tree) walk(root, []);
  return out;
}

export default function AddPage() {
  const { t, lang } = useLang();
  const [rows, setRows] = useState<FormRow[]>([emptyRow()]);
  const [submitting, setSubmitting] = useState(false);
  const [tree, setTree] = useState<Category[]>([]);

  const fetchTree = useCallback(async () => {
    try {
      const data = await api.listCategories({ tree: true });
      setTree(data);
    } catch (e) {
      toast.error((e as Error).message);
    }
  }, []);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  const leafOptions = useMemo(() => collectLeaves(tree, lang), [tree, lang]);

  const updateRow = (index: number, field: keyof FormRow, value: string) => {
    setRows((prev) =>
      prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)),
    );
  };

  const addRow = () => setRows((prev) => [...prev, emptyRow()]);

  const removeRow = (index: number) => {
    if (rows.length <= 1) return;
    setRows((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    for (const row of rows) {
      if (!row.name || !row.name_en || !row.name_zh) {
        toast.error(t("error") + ": " + t("name") + " / " + t("nameEn") + " / " + t("nameZh"));
        return;
      }
      if (!row.category_id) {
        toast.error(t("pickLeafCategory"));
        return;
      }
    }

    setSubmitting(true);
    try {
      const items: CodenameInput[] = rows.map(
        ({ name, name_en, name_zh, category_id, brief }) => ({
          name,
          name_en,
          name_zh,
          category_id,
          brief,
        }),
      );
      const result = await api.addCodenames(items);
      if (result.errors.length > 0) {
        result.errors.forEach((e) => toast.error(e));
      }
      if (result.added > 0) {
        toast.success(`${t("addSuccess")} (${result.added})`);
        setRows([emptyRow()]);
      }
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      {rows.map((row, index) => (
        <Card key={row.key}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                {t("codenames")} #{index + 1}
              </CardTitle>
              {rows.length > 1 && (
                <Button variant="ghost" size="icon" onClick={() => removeRow(index)}>
                  <Trash2 className="h-4 w-4 text-muted-foreground" />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="grid gap-2">
                  <Label>{t("name")} *</Label>
                  <Input
                    value={row.name}
                    onChange={(e) => updateRow(index, "name", e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>{t("nameEn")} *</Label>
                  <Input
                    value={row.name_en}
                    onChange={(e) => updateRow(index, "name_en", e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>{t("nameZh")} *</Label>
                  <Input
                    value={row.name_zh}
                    onChange={(e) => updateRow(index, "name_zh", e.target.value)}
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label>
                  {t("category")} * <span className="text-xs text-muted-foreground">({t("leafOnly")})</span>
                </Label>
                <Select
                  value={row.category_id}
                  onValueChange={(v) => updateRow(index, "category_id", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={t("pickLeafCategory")} />
                  </SelectTrigger>
                  <SelectContent>
                    {leafOptions.map((opt) => (
                      <SelectItem key={opt.category_id} value={opt.category_id}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>{t("brief")} *</Label>
                <Textarea
                  value={row.brief}
                  onChange={(e) => updateRow(index, "brief", e.target.value)}
                  rows={2}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      <div className="flex gap-3">
        <Button variant="outline" onClick={addRow} className="gap-2">
          <Plus className="h-4 w-4" />
          {t("addMore")}
        </Button>
        <Button onClick={handleSubmit} disabled={submitting} className="gap-2">
          <Send className="h-4 w-4" />
          {t("submit")}
        </Button>
      </div>
    </div>
  );
}

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Trash2, Send } from "lucide-react";
import { toast } from "sonner";
import { api, type CodenameInput } from "@/lib/api";
import { useLang } from "@/hooks/use-lang";

const SUB_THEMES = [
  "philosophy", "art", "science", "economics", "literature",
  "music", "politics", "medicine", "mathematics", "engineering",
];

interface FormRow extends CodenameInput {
  key: number;
}

let nextKey = 1;
function emptyRow(): FormRow {
  return { key: nextKey++, name: "", name_en: "", name_zh: "", theme: "person", sub_theme: "", brief: "" };
}

export default function AddPage() {
  const { t } = useLang();
  const [rows, setRows] = useState<FormRow[]>([emptyRow()]);
  const [submitting, setSubmitting] = useState(false);

  const updateRow = (index: number, field: keyof CodenameInput, value: string) => {
    setRows((prev) =>
      prev.map((r, i) => {
        if (i !== index) return r;
        const updated = { ...r, [field]: value };
        if (field === "theme" && value === "animal") {
          updated.sub_theme = null;
        }
        return updated;
      })
    );
  };

  const addRow = () => setRows((prev) => [...prev, emptyRow()]);

  const removeRow = (index: number) => {
    if (rows.length <= 1) return;
    setRows((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    // Validate
    for (const row of rows) {
      if (!row.name || !row.name_en || !row.name_zh || !row.brief) {
        toast.error(t("error") + ": " + t("name") + " / " + t("brief") + " required");
        return;
      }
      if (row.theme === "person" && !row.sub_theme) {
        toast.error(t("personRequired"));
        return;
      }
    }

    setSubmitting(true);
    try {
      const items: CodenameInput[] = rows.map(({ name, name_en, name_zh, theme, sub_theme, brief }) => ({
        name,
        name_en,
        name_zh,
        theme,
        sub_theme: theme === "animal" ? null : sub_theme,
        brief,
      }));
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
                  <Input value={row.name} onChange={(e) => updateRow(index, "name", e.target.value)} />
                </div>
                <div className="grid gap-2">
                  <Label>{t("nameEn")} *</Label>
                  <Input value={row.name_en} onChange={(e) => updateRow(index, "name_en", e.target.value)} />
                </div>
                <div className="grid gap-2">
                  <Label>{t("nameZh")} *</Label>
                  <Input value={row.name_zh} onChange={(e) => updateRow(index, "name_zh", e.target.value)} />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-2">
                  <Label>{t("theme")} *</Label>
                  <Select value={row.theme} onValueChange={(v) => updateRow(index, "theme", v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="person">{t("person")}</SelectItem>
                      <SelectItem value="animal">{t("animal")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {row.theme === "person" && (
                  <div className="grid gap-2">
                    <Label>{t("subTheme")} *</Label>
                    <Select value={row.sub_theme || ""} onValueChange={(v) => updateRow(index, "sub_theme", v)}>
                      <SelectTrigger>
                        <SelectValue placeholder={t("subTheme")} />
                      </SelectTrigger>
                      <SelectContent>
                        {SUB_THEMES.map((st) => (
                          <SelectItem key={st} value={st}>{st}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
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

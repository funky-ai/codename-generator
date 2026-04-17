import { useState } from "react";
import { Card, CardContent } from "@shared/components/ui/card";
import { Badge } from "@shared/components/ui/badge";
import { Button } from "@shared/components/ui/button";
import { Input } from "@shared/components/ui/input";
import { Label } from "@shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@shared/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@shared/components/ui/dialog";
import { Shuffle, Link } from "lucide-react";
import { toast } from "sonner";
import { api, type Codename } from "@shared/lib/api";
import { useLang } from "@/lib/admin-i18n";

export default function DrawPage() {
  const { t } = useLang();
  const [count, setCount] = useState(3);
  const [theme, setTheme] = useState("all");
  const [results, setResults] = useState<Codename[]>([]);
  const [loading, setLoading] = useState(false);

  // Assign dialog
  const [assignTarget, setAssignTarget] = useState<Codename | null>(null);
  const [assignDesc, setAssignDesc] = useState("");

  const handleDraw = async () => {
    setLoading(true);
    try {
      const data = await api.drawRandom(count, theme === "all" ? undefined : theme);
      setResults(data);
      if (data.length === 0) {
        toast.info(t("noData"));
      }
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleAssign = async () => {
    if (!assignTarget) return;
    try {
      await api.assignCodename(assignTarget.codename_id, assignDesc || undefined);
      toast.success(t("assignSuccess"));
      setAssignTarget(null);
      setAssignDesc("");
      // Remove assigned from results
      setResults((prev) => prev.filter((c) => c.codename_id !== assignTarget.codename_id));
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="grid gap-2 w-full sm:w-auto">
              <Label>{t("count")}</Label>
              <Input
                type="number"
                min={1}
                max={10}
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="w-full sm:w-[100px]"
              />
            </div>
            <div className="grid gap-2 w-full sm:w-auto">
              <Label>{t("theme")}</Label>
              <Select value={theme} onValueChange={setTheme}>
                <SelectTrigger className="w-full sm:w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t("all")}</SelectItem>
                  <SelectItem value="person">{t("person")}</SelectItem>
                  <SelectItem value="animal">{t("animal")}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleDraw} disabled={loading} className="gap-2 w-full sm:w-auto">
              <Shuffle className="h-4 w-4" />
              {t("drawRandom")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {results.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((c) => (
            <Card key={c.codename_id}>
              <CardContent className="pt-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="font-semibold text-lg">{c.name}</div>
                  <Badge variant={c.theme === "person" ? "default" : "secondary"}>
                    {c.theme === "person" ? t("person") : t("animal")}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground mb-1">
                  {c.name_en} / {c.name_zh}
                </div>
                {c.sub_theme && (
                  <div className="text-xs text-muted-foreground mb-2">{t("subTheme")}: {c.sub_theme}</div>
                )}
                <p className="text-sm mb-4">{c.brief}</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setAssignTarget(c)}
                  className="w-full gap-2"
                >
                  <Link className="h-3 w-3" />
                  {t("assign")}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Assign dialog */}
      <Dialog open={!!assignTarget} onOpenChange={(open) => !open && setAssignTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("assign")} — {assignTarget?.name}</DialogTitle>
          </DialogHeader>
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            {t("assignConfirm")}
          </div>
          <div className="grid gap-2 py-2">
            <Label>{t("description")}</Label>
            <Input
              value={assignDesc}
              onChange={(e) => setAssignDesc(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAssignTarget(null)}>{t("cancel")}</Button>
            <Button variant="destructive" onClick={handleAssign}>{t("confirm")}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

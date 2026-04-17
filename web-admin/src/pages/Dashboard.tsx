import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@shared/components/ui/card";
import { Button } from "@shared/components/ui/button";
import { AlertTriangle, Database, FolderTree, Plus, Shuffle } from "lucide-react";
import { api, type InventoryStats } from "@shared/lib/api";
import { useLang } from "@/lib/admin-i18n";

interface Props {
  onNavigate: (page: "inventory" | "add" | "draw" | "categories") => void;
}

export default function DashboardPage({ onNavigate }: Props) {
  const { t, lang } = useLang();
  const [stats, setStats] = useState<InventoryStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStats().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-muted-foreground text-center py-12">{t("loading")}</div>;
  }

  if (!stats) return null;

  // Top-level rows for the headline section; sub-category rows (with data)
  // flat-listed below. The stats endpoint reports per-category direct counts
  // only — consumers aggregate up the tree themselves, by design.
  const tops = stats.by_category.filter((c) => c.depth === 1);
  const leafRows = stats.by_category.filter((c) => c.depth > 1 && c.total > 0);

  return (
    <div className="space-y-6">
      {stats.low_stock_warning && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-800">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span className="text-sm">{stats.warning_message}</span>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t("total")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t("available")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{stats.available}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t("assigned")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600">{stats.assigned}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("categoryBreakdown")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {tops.length === 0 && (
              <div className="text-muted-foreground text-sm">{t("noData")}</div>
            )}
            {tops.map((row) => (
              <div
                key={row.category_id}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="font-medium">
                  {lang === "zh" ? row.name_zh : row.name_en}
                  <span className="text-xs text-muted-foreground ml-2">({row.slug})</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  {row.total} {t("total")} / {row.available} {t("available")}
                </div>
              </div>
            ))}
          </div>

          {leafRows.length > 0 && (
            <>
              <h4 className="text-sm font-medium mt-6 mb-2 text-muted-foreground">
                {t("categories")} ({t("byCategory")})
              </h4>
              <div className="space-y-1 text-sm">
                {leafRows.map((row) => (
                  <div
                    key={row.category_id}
                    className="flex items-center justify-between rounded border p-2"
                  >
                    <div>
                      <span className="text-xs text-muted-foreground">
                        {"—".repeat(row.depth - 1)}
                      </span>{" "}
                      {lang === "zh" ? row.name_zh : row.name_en}
                      <span className="text-xs text-muted-foreground ml-2">({row.slug})</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {row.total} / {row.available} {t("available")}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("quickActions")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => onNavigate("inventory")} variant="outline" className="gap-2">
              <Database className="h-4 w-4" />
              {t("inventory")}
            </Button>
            <Button onClick={() => onNavigate("add")} variant="outline" className="gap-2">
              <Plus className="h-4 w-4" />
              {t("add")}
            </Button>
            <Button onClick={() => onNavigate("draw")} variant="outline" className="gap-2">
              <Shuffle className="h-4 w-4" />
              {t("drawRandom")}
            </Button>
            <Button onClick={() => onNavigate("categories")} variant="outline" className="gap-2">
              <FolderTree className="h-4 w-4" />
              {t("categories")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

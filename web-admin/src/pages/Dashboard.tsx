import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Database, Plus, Shuffle, AlertTriangle } from "lucide-react";
import { api, type InventoryStats } from "@/lib/api";
import { useLang } from "@/hooks/use-lang";

interface Props {
  onNavigate: (page: "inventory" | "add" | "draw") => void;
}

export default function DashboardPage({ onNavigate }: Props) {
  const { t } = useLang();
  const [stats, setStats] = useState<InventoryStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStats().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-muted-foreground text-center py-12">{t("loading")}</div>;
  }

  if (!stats) return null;

  return (
    <div className="space-y-6">
      {/* Low stock warning */}
      {stats.low_stock_warning && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-800">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span className="text-sm">{stats.warning_message}</span>
        </div>
      )}

      {/* Stats cards */}
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

      {/* Theme breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("themeBreakdown")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(stats.by_theme).map(([theme, count]) => (
              <div
                key={theme}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center gap-2">
                  <Badge variant={theme === "person" ? "default" : "secondary"}>
                    {theme === "person" ? t("person") : t("animal")}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground">
                  {count} {t("total")} / {stats.available_by_theme[theme] || 0} {t("available")}
                </div>
              </div>
            ))}
            {Object.keys(stats.by_theme).length === 0 && (
              <div className="text-muted-foreground text-sm col-span-2">{t("noData")}</div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Quick actions */}
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
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

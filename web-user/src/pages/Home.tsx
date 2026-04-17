import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@shared/components/ui/card";
import { Button } from "@shared/components/ui/button";
import { Database, Shuffle } from "lucide-react";
import { api, type InventoryStats } from "@shared/lib/api";
import { useLang } from "@/lib/user-i18n";

interface Props {
  onNavigate: (page: "browse" | "draw") => void;
}

export default function HomePage({ onNavigate }: Props) {
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
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t("availableNow")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-green-600">{stats.available}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t("totalLibrary")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t("allAssigned")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-amber-600">{stats.assigned}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("getStarted")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={() => onNavigate("draw")}
              size="lg"
              className="gap-2"
              disabled={stats.available === 0}
            >
              <Shuffle className="h-5 w-5" />
              {t("pickOne")}
            </Button>
            <Button
              onClick={() => onNavigate("browse")}
              size="lg"
              variant="outline"
              className="gap-2"
            >
              <Database className="h-5 w-5" />
              {t("browseAll")}
            </Button>
          </div>
          {stats.total === 0 && (
            <p className="mt-4 text-sm text-muted-foreground">{t("emptyHint")}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

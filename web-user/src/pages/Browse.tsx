import { useEffect, useState, useCallback } from "react";
import { Card, CardContent } from "@shared/components/ui/card";
import { Badge } from "@shared/components/ui/badge";
import { Input } from "@shared/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@shared/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@shared/components/ui/table";
import { Search } from "lucide-react";
import { api, type Codename } from "@shared/lib/api";
import { useLang } from "@/lib/user-i18n";

export default function BrowsePage() {
  const { t } = useLang();
  const [codenames, setCodenames] = useState<Codename[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [themeFilter, setThemeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (searchQuery.trim()) {
        const results = await api.searchCodenames(searchQuery);
        setCodenames(results);
      } else {
        const results = await api.getCodenames({
          theme: themeFilter === "all" ? undefined : themeFilter,
          status: statusFilter === "all" ? undefined : statusFilter,
        });
        setCodenames(results);
      }
    } finally {
      setLoading(false);
    }
  }, [searchQuery, themeFilter, statusFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("search") + "..."}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={themeFilter} onValueChange={setThemeFilter}>
          <SelectTrigger className="w-full sm:w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("all")} {t("theme")}</SelectItem>
            <SelectItem value="person">{t("person")}</SelectItem>
            <SelectItem value="animal">{t("animal")}</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("all")} {t("status")}</SelectItem>
            <SelectItem value="available">{t("available")}</SelectItem>
            <SelectItem value="assigned">{t("assigned")}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="text-center py-12 text-muted-foreground">{t("loading")}</div>
      ) : codenames.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          {searchQuery.trim() ? t("noMatches") : t("noData")}
        </div>
      ) : (
        <>
          <div className="hidden md:block rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("name")}</TableHead>
                  <TableHead>{t("nameEn")}</TableHead>
                  <TableHead>{t("nameZh")}</TableHead>
                  <TableHead>{t("theme")}</TableHead>
                  <TableHead>{t("status")}</TableHead>
                  <TableHead>{t("brief")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {codenames.map((c) => (
                  <TableRow key={c.codename_id}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell>{c.name_en}</TableCell>
                    <TableCell>{c.name_zh}</TableCell>
                    <TableCell>
                      <Badge variant={c.theme === "person" ? "default" : "secondary"}>
                        {c.theme === "person" ? t("person") : t("animal")}
                      </Badge>
                      {c.sub_theme && (
                        <span className="ml-1 text-xs text-muted-foreground">{c.sub_theme}</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={c.status === "available" ? "outline" : "secondary"}
                        className={c.status === "available" ? "border-green-300 text-green-700" : ""}
                      >
                        {c.status === "available" ? t("available") : t("assigned")}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[240px] truncate text-sm text-muted-foreground">
                      {c.brief}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="md:hidden space-y-3">
            {codenames.map((c) => (
              <Card key={c.codename_id}>
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="font-medium">{c.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {c.name_en} / {c.name_zh}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Badge variant={c.theme === "person" ? "default" : "secondary"}>
                        {c.theme === "person" ? t("person") : t("animal")}
                      </Badge>
                      <Badge
                        variant={c.status === "available" ? "outline" : "secondary"}
                        className={c.status === "available" ? "border-green-300 text-green-700" : ""}
                      >
                        {c.status === "available" ? t("available") : t("assigned")}
                      </Badge>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">{c.brief}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent } from "@shared/components/ui/card";
import { Badge } from "@shared/components/ui/badge";
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
import { api, type LogEntry } from "@shared/lib/api";
import { useLang } from "@/lib/admin-i18n";

const actionColor: Record<string, string> = {
  added: "border-green-300 text-green-700",
  assigned: "border-amber-300 text-amber-700",
  updated: "border-blue-300 text-blue-700",
};

export default function LogsPage() {
  const { t } = useLang();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState("all");
  const [limit, setLimit] = useState("50");

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getLogs(
        Number(limit),
        actionFilter === "all" ? undefined : actionFilter
      );
      setLogs(data);
    } finally {
      setLoading(false);
    }
  }, [actionFilter, limit]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const formatDetails = (details: string | null): string => {
    if (!details) return "—";
    try {
      const parsed = JSON.parse(details);
      if (parsed.name) return parsed.name;
      return details;
    } catch {
      return details;
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-3">
        <Select value={actionFilter} onValueChange={setActionFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("all")} {t("action")}</SelectItem>
            <SelectItem value="added">{t("added")}</SelectItem>
            <SelectItem value="assigned">{t("assigned")}</SelectItem>
            <SelectItem value="updated">{t("updated")}</SelectItem>
          </SelectContent>
        </Select>
        <Select value={limit} onValueChange={setLimit}>
          <SelectTrigger className="w-[100px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="25">25</SelectItem>
            <SelectItem value="50">50</SelectItem>
            <SelectItem value="100">100</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="text-center py-12 text-muted-foreground">{t("loading")}</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">{t("noData")}</div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("timestamp")}</TableHead>
                  <TableHead>{t("action")}</TableHead>
                  <TableHead>ID</TableHead>
                  <TableHead>{t("operator")}</TableHead>
                  <TableHead>{t("details")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log, i) => (
                  <TableRow key={i}>
                    <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                      {log.timestamp}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={actionColor[log.action] || ""}>
                        {log.action}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs">{log.codename_id}</TableCell>
                    <TableCell>{log.operator}</TableCell>
                    <TableCell className="max-w-[200px] truncate text-sm text-muted-foreground">
                      {formatDetails(log.details)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {logs.map((log, i) => (
              <Card key={i}>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="outline" className={actionColor[log.action] || ""}>
                      {log.action}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{log.timestamp}</span>
                  </div>
                  <div className="text-xs font-mono text-muted-foreground mb-1">
                    {log.codename_id}
                  </div>
                  <div className="text-sm">
                    {t("operator")}: {log.operator}
                  </div>
                  {log.details && (
                    <div className="text-sm text-muted-foreground mt-1">
                      {formatDetails(log.details)}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

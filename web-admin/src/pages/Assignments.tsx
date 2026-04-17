import { useEffect, useState } from "react";
import { Card, CardContent } from "@shared/components/ui/card";
import { Badge } from "@shared/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@shared/components/ui/table";
import { api, type Assignment } from "@shared/lib/api";
import { useLang } from "@/lib/admin-i18n";

export default function AssignmentsPage() {
  const { t } = useLang();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAssignments().then(setAssignments).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center py-12 text-muted-foreground">{t("loading")}</div>;
  }

  if (assignments.length === 0) {
    return <div className="text-center py-12 text-muted-foreground">{t("noData")}</div>;
  }

  return (
    <div>
      {/* Desktop table */}
      <div className="hidden md:block rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("name")}</TableHead>
              <TableHead>ID</TableHead>
              <TableHead>{t("description")}</TableHead>
              <TableHead>{t("assignedBy")}</TableHead>
              <TableHead>{t("timestamp")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {assignments.map((a) => (
              <TableRow key={a.assignment_id}>
                <TableCell className="font-medium">{a.codename_name}</TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">{a.codename_id}</TableCell>
                <TableCell>{a.description || "—"}</TableCell>
                <TableCell>
                  <Badge variant="outline">{a.assigned_by}</Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">{a.assigned_at}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-3">
        {assignments.map((a) => (
          <Card key={a.assignment_id}>
            <CardContent className="pt-4">
              <div className="flex items-start justify-between mb-1">
                <div className="font-medium">{a.codename_name}</div>
                <Badge variant="outline">{a.assigned_by}</Badge>
              </div>
              <div className="text-xs font-mono text-muted-foreground mb-2">{a.codename_id}</div>
              {a.description && <p className="text-sm mb-2">{a.description}</p>}
              <div className="text-xs text-muted-foreground">{a.assigned_at}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent } from "@shared/components/ui/card";
import { Badge } from "@shared/components/ui/badge";
import { Button } from "@shared/components/ui/button";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@shared/components/ui/dialog";
import { Label } from "@shared/components/ui/label";
import { Textarea } from "@shared/components/ui/textarea";
import { Search, Pencil, Link } from "lucide-react";
import { toast } from "sonner";
import { api, type Codename } from "@shared/lib/api";
import { useLang } from "@/lib/admin-i18n";

export default function InventoryPage() {
  const { t } = useLang();
  const [codenames, setCodenames] = useState<Codename[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [themeFilter, setThemeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  // Edit dialog
  const [editTarget, setEditTarget] = useState<Codename | null>(null);
  const [editForm, setEditForm] = useState({ name: "", name_en: "", name_zh: "", brief: "" });

  // Assign dialog
  const [assignTarget, setAssignTarget] = useState<Codename | null>(null);
  const [assignDesc, setAssignDesc] = useState("");

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

  const handleEdit = async () => {
    if (!editTarget) return;
    try {
      await api.updateCodename(editTarget.codename_id, editForm);
      toast.success(t("updateSuccess"));
      setEditTarget(null);
      fetchData();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleAssign = async () => {
    if (!assignTarget) return;
    try {
      await api.assignCodename(assignTarget.codename_id, assignDesc || undefined);
      toast.success(t("assignSuccess"));
      setAssignTarget(null);
      setAssignDesc("");
      fetchData();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const openEdit = (c: Codename) => {
    setEditForm({ name: c.name, name_en: c.name_en, name_zh: c.name_zh, brief: c.brief });
    setEditTarget(c);
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
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
        <div className="text-center py-12 text-muted-foreground">{t("noData")}</div>
      ) : (
        <>
          {/* Desktop table */}
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
                  <TableHead className="w-[100px]"></TableHead>
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
                      <Badge variant={c.status === "available" ? "outline" : "secondary"}
                        className={c.status === "available" ? "border-green-300 text-green-700" : ""}
                      >
                        {c.status === "available" ? t("available") : t("assigned")}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate text-sm text-muted-foreground">
                      {c.brief}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" onClick={() => openEdit(c)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        {c.status === "available" && (
                          <Button variant="ghost" size="icon" onClick={() => setAssignTarget(c)}>
                            <Link className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile cards */}
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
                  <p className="text-sm text-muted-foreground mb-3">{c.brief}</p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => openEdit(c)} className="gap-1">
                      <Pencil className="h-3 w-3" />
                      {t("edit")}
                    </Button>
                    {c.status === "available" && (
                      <Button variant="outline" size="sm" onClick={() => setAssignTarget(c)} className="gap-1">
                        <Link className="h-3 w-3" />
                        {t("assign")}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Edit dialog */}
      <Dialog open={!!editTarget} onOpenChange={(open) => !open && setEditTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("edit")} — {editTarget?.name}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t("name")}</Label>
              <Input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>{t("nameEn")}</Label>
                <Input value={editForm.name_en} onChange={(e) => setEditForm({ ...editForm, name_en: e.target.value })} />
              </div>
              <div className="grid gap-2">
                <Label>{t("nameZh")}</Label>
                <Input value={editForm.name_zh} onChange={(e) => setEditForm({ ...editForm, name_zh: e.target.value })} />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>{t("brief")}</Label>
              <Textarea value={editForm.brief} onChange={(e) => setEditForm({ ...editForm, brief: e.target.value })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditTarget(null)}>{t("cancel")}</Button>
            <Button onClick={handleEdit}>{t("submit")}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
              placeholder={t("description") + " (" + t("status") + ")"}
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

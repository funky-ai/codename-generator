import { useCallback, useEffect, useMemo, useState } from "react";
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
import { Link, Pencil, Search } from "lucide-react";
import { toast } from "sonner";
import { api, type Category, type Codename } from "@shared/lib/api";
import { useLang } from "@/lib/admin-i18n";

interface CategoryOption {
  category_id: string;
  label: string;
  depth: number;
  isLeaf: boolean;
}

function collectAll(tree: Category[], lang: "zh" | "en"): CategoryOption[] {
  const out: CategoryOption[] = [];
  const walk = (node: Category, path: string[]) => {
    const displayName = lang === "zh" ? node.name_zh : node.name_en;
    const nextPath = [...path, displayName];
    out.push({
      category_id: node.category_id,
      label: nextPath.join(" › "),
      depth: node.depth,
      isLeaf: !node.children || node.children.length === 0,
    });
    if (node.children) for (const child of node.children) walk(child, nextPath);
  };
  for (const root of tree) walk(root, []);
  return out;
}

function collectLeaves(all: CategoryOption[]): CategoryOption[] {
  return all.filter((c) => c.isLeaf);
}

export default function InventoryPage() {
  const { t, lang } = useLang();
  const [codenames, setCodenames] = useState<Codename[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [tree, setTree] = useState<Category[]>([]);

  // Edit dialog
  const [editTarget, setEditTarget] = useState<Codename | null>(null);
  const [editForm, setEditForm] = useState({
    name: "",
    name_en: "",
    name_zh: "",
    category_id: "",
    brief: "",
  });

  // Assign dialog
  const [assignTarget, setAssignTarget] = useState<Codename | null>(null);
  const [assignDesc, setAssignDesc] = useState("");

  const fetchTree = useCallback(async () => {
    try {
      const data = await api.listCategories({ tree: true });
      setTree(data);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  const allOptions = useMemo(() => collectAll(tree, lang), [tree, lang]);
  const leafOptions = useMemo(() => collectLeaves(allOptions), [allOptions]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (searchQuery.trim()) {
        const results = await api.searchCodenames(searchQuery);
        setCodenames(results);
      } else {
        const results = await api.getCodenames({
          category_id: categoryFilter === "all" ? undefined : categoryFilter,
          status: statusFilter === "all" ? undefined : statusFilter,
        });
        setCodenames(results);
      }
    } finally {
      setLoading(false);
    }
  }, [searchQuery, categoryFilter, statusFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleEdit = async () => {
    if (!editTarget) return;
    try {
      const patch: {
        name?: string;
        name_en?: string;
        name_zh?: string;
        brief?: string;
        category_id?: string;
      } = {
        name: editForm.name,
        name_en: editForm.name_en,
        name_zh: editForm.name_zh,
        brief: editForm.brief,
      };
      if (editForm.category_id && editForm.category_id !== editTarget.category_id) {
        patch.category_id = editForm.category_id;
      }
      await api.updateCodename(editTarget.codename_id, patch);
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
    setEditForm({
      name: c.name,
      name_en: c.name_en,
      name_zh: c.name_zh,
      category_id: c.category_id,
      brief: c.brief,
    });
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
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-full sm:w-[220px]">
            <SelectValue placeholder={t("category")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("all")} {t("category")}</SelectItem>
            {allOptions.map((opt) => (
              <SelectItem key={opt.category_id} value={opt.category_id}>
                {opt.label}
              </SelectItem>
            ))}
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
                  <TableHead>{t("category")}</TableHead>
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
                      <span className="text-xs text-muted-foreground">
                        {c.category_path.join(" › ")}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={c.status === "available" ? "outline" : "secondary"}
                        className={
                          c.status === "available"
                            ? "border-green-300 text-green-700"
                            : ""
                        }
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
                      <div className="text-xs text-muted-foreground">
                        {c.category_path.join(" › ")}
                      </div>
                    </div>
                    <Badge
                      variant={c.status === "available" ? "outline" : "secondary"}
                      className={
                        c.status === "available"
                          ? "border-green-300 text-green-700"
                          : ""
                      }
                    >
                      {c.status === "available" ? t("available") : t("assigned")}
                    </Badge>
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
            <DialogTitle>
              {t("edit")} — {editTarget?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t("name")}</Label>
              <Input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>{t("nameEn")}</Label>
                <Input
                  value={editForm.name_en}
                  onChange={(e) => setEditForm({ ...editForm, name_en: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label>{t("nameZh")}</Label>
                <Input
                  value={editForm.name_zh}
                  onChange={(e) => setEditForm({ ...editForm, name_zh: e.target.value })}
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>
                {t("category")}{" "}
                <span className="text-xs text-muted-foreground">({t("leafOnly")})</span>
              </Label>
              <Select
                value={editForm.category_id}
                onValueChange={(v) => setEditForm({ ...editForm, category_id: v })}
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
              <Label>{t("brief")}</Label>
              <Textarea
                value={editForm.brief}
                onChange={(e) => setEditForm({ ...editForm, brief: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditTarget(null)}>
              {t("cancel")}
            </Button>
            <Button onClick={handleEdit}>{t("submit")}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign dialog */}
      <Dialog open={!!assignTarget} onOpenChange={(open) => !open && setAssignTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {t("assign")} — {assignTarget?.name}
            </DialogTitle>
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
            <Button variant="outline" onClick={() => setAssignTarget(null)}>
              {t("cancel")}
            </Button>
            <Button variant="destructive" onClick={handleAssign}>
              {t("confirm")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

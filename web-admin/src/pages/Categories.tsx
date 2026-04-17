import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@shared/components/ui/card";
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@shared/components/ui/dialog";
import { ChevronDown, ChevronRight, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, type Category } from "@shared/lib/api";
import { useLang } from "@/lib/admin-i18n";

const MAX_DEPTH = 3;

interface CategoryRowProps {
  category: Category;
  expanded: Set<string>;
  toggle: (id: string) => void;
  onSelect: (cat: Category) => void;
  selectedId: string | null;
  lang: "zh" | "en";
}

function CategoryRow({ category, expanded, toggle, onSelect, selectedId, lang }: CategoryRowProps) {
  const hasChildren = !!category.children && category.children.length > 0;
  const isOpen = expanded.has(category.category_id);
  const indent = (category.depth - 1) * 16;
  const label = lang === "zh" ? category.name_zh : category.name_en;
  return (
    <>
      <button
        type="button"
        onClick={() => onSelect(category)}
        className={`w-full flex items-center gap-2 py-1.5 px-2 text-left rounded hover:bg-muted/50 ${
          selectedId === category.category_id ? "bg-muted" : ""
        }`}
        style={{ paddingLeft: indent + 8 }}
      >
        {hasChildren ? (
          <span
            role="button"
            onClick={(e) => {
              e.stopPropagation();
              toggle(category.category_id);
            }}
            className="inline-flex items-center justify-center w-4 h-4 shrink-0"
          >
            {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          </span>
        ) : (
          <span className="inline-block w-4 h-4 shrink-0" />
        )}
        <span className="text-sm flex-1 truncate">{label}</span>
        <span className="text-xs text-muted-foreground">{category.slug}</span>
        {category.is_archived ? (
          <Badge variant="secondary" className="text-xs">
            {category.depth}/{MAX_DEPTH}
          </Badge>
        ) : (
          <span className="text-xs text-muted-foreground">
            {category.depth}/{MAX_DEPTH}
          </span>
        )}
      </button>
      {hasChildren && isOpen && category.children!.map((child) => (
        <CategoryRow
          key={child.category_id}
          category={child}
          expanded={expanded}
          toggle={toggle}
          onSelect={onSelect}
          selectedId={selectedId}
          lang={lang}
        />
      ))}
    </>
  );
}

function flatten(tree: Category[]): Category[] {
  const out: Category[] = [];
  const walk = (nodes: Category[]) => {
    for (const n of nodes) {
      out.push(n);
      if (n.children) walk(n.children);
    }
  };
  walk(tree);
  return out;
}

function computeSubtreeHeight(category: Category): number {
  if (!category.children || category.children.length === 0) return 1;
  return 1 + Math.max(...category.children.map(computeSubtreeHeight));
}

export default function CategoriesPage() {
  const { t, lang } = useLang();
  const [tree, setTree] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());
  const [includeArchived, setIncludeArchived] = useState(false);
  const [selected, setSelected] = useState<Category | null>(null);
  const [form, setForm] = useState({
    slug: "",
    name_en: "",
    name_zh: "",
    parent_category_id: "" as string,
    sort_order: 0,
    is_archived: false,
  });
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    slug: "",
    name_en: "",
    name_zh: "",
    parent_category_id: "" as string,
    sort_order: 0,
  });

  const fetchTree = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listCategories({ tree: true, include_archived: includeArchived });
      setTree(data);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [includeArchived]);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  // Auto-expand top-level once after the tree first arrives. A ref guard keeps
  // this from reapplying after the user manually collapses everything.
  const autoExpandedRef = useRef(false);
  useEffect(() => {
    if (!autoExpandedRef.current && tree.length > 0) {
      autoExpandedRef.current = true;
      setExpanded(new Set(tree.map((r) => r.category_id)));
    }
  }, [tree]);

  const flat = useMemo(() => flatten(tree), [tree]);

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const handleSelect = (cat: Category) => {
    setSelected(cat);
    setForm({
      slug: cat.slug,
      name_en: cat.name_en,
      name_zh: cat.name_zh,
      parent_category_id: cat.parent_category_id ?? "",
      sort_order: cat.sort_order,
      is_archived: cat.is_archived,
    });
  };

  // Candidates usable as parents for the currently-selected category.
  const parentCandidates = useMemo(() => {
    if (!selected) return flat;
    const subtreeHeight = computeSubtreeHeight(selected);
    return flat.filter((c) => {
      if (c.category_id === selected.category_id) return false;
      if (c.is_archived) return false;
      // New depth of this subtree: c.depth + subtreeHeight ≤ MAX_DEPTH.
      return c.depth + subtreeHeight <= MAX_DEPTH;
    });
  }, [selected, flat]);

  const createParentCandidates = useMemo(
    () => flat.filter((c) => !c.is_archived && c.depth < MAX_DEPTH),
    [flat],
  );

  const handleSave = async () => {
    if (!selected) return;
    try {
      await api.updateCategory(selected.category_id, {
        slug: form.slug !== selected.slug ? form.slug : undefined,
        name_en: form.name_en !== selected.name_en ? form.name_en : undefined,
        name_zh: form.name_zh !== selected.name_zh ? form.name_zh : undefined,
        parent_category_id:
          form.parent_category_id !== (selected.parent_category_id ?? "")
            ? form.parent_category_id
            : undefined,
        sort_order:
          form.sort_order !== selected.sort_order ? form.sort_order : undefined,
        is_archived:
          form.is_archived !== selected.is_archived ? form.is_archived : undefined,
      });
      toast.success(t("updateSuccess"));
      await fetchTree();
      // Re-select by id after refresh
      setSelected(null);
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;
    if (!window.confirm(t("deleteConfirm"))) return;
    try {
      await api.deleteCategory(selected.category_id);
      toast.success(t("deleteSuccess"));
      setSelected(null);
      fetchTree();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleCreate = async () => {
    try {
      await api.createCategory({
        slug: createForm.slug,
        name_en: createForm.name_en,
        name_zh: createForm.name_zh,
        parent_category_id: createForm.parent_category_id || null,
        sort_order: createForm.sort_order,
      });
      toast.success(t("categoryAdded"));
      setCreateOpen(false);
      setCreateForm({
        slug: "",
        name_en: "",
        name_zh: "",
        parent_category_id: "",
        sort_order: 0,
      });
      fetchTree();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Left: tree */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base">{t("categories")}</CardTitle>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={includeArchived}
                  onChange={(e) => setIncludeArchived(e.target.checked)}
                />
                {t("showArchived")}
              </label>
              <Button
                size="sm"
                onClick={() => setCreateOpen(true)}
                className="gap-1"
              >
                <Plus className="h-4 w-4" />
                {t("new")}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-2">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              {t("loading")}
            </div>
          ) : tree.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              {t("noData")}
            </div>
          ) : (
            <div className="max-h-[70vh] overflow-auto">
              {tree.map((root) => (
                <CategoryRow
                  key={root.category_id}
                  category={root}
                  expanded={expanded}
                  toggle={toggle}
                  onSelect={handleSelect}
                  selectedId={selected?.category_id ?? null}
                  lang={lang}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Right: edit form */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            {selected ? t("edit") : t("categories")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selected ? (
            <div className="space-y-4">
              <div className="grid gap-2">
                <Label>{t("slug")} *</Label>
                <Input
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-2">
                  <Label>{t("nameEn")} *</Label>
                  <Input
                    value={form.name_en}
                    onChange={(e) => setForm({ ...form, name_en: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>{t("nameZh")} *</Label>
                  <Input
                    value={form.name_zh}
                    onChange={(e) => setForm({ ...form, name_zh: e.target.value })}
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label>{t("parent")}</Label>
                <Select
                  value={form.parent_category_id || "__top__"}
                  onValueChange={(v) =>
                    setForm({
                      ...form,
                      parent_category_id: v === "__top__" ? "" : v,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__top__">
                      — {t("rootLevel")} —
                    </SelectItem>
                    {parentCandidates.map((c) => (
                      <SelectItem key={c.category_id} value={c.category_id}>
                        {" ".repeat((c.depth - 1) * 2)}
                        {(lang === "zh" ? c.name_zh : c.name_en) + ` (${c.slug})`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {t("depthLimitHint")}
                </p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-2">
                  <Label>{t("sortOrder")}</Label>
                  <Input
                    type="number"
                    value={form.sort_order}
                    onChange={(e) =>
                      setForm({ ...form, sort_order: Number(e.target.value) })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label>{t("archived")}</Label>
                  <label className="inline-flex items-center gap-2 mt-2">
                    <input
                      type="checkbox"
                      checked={form.is_archived}
                      onChange={(e) =>
                        setForm({ ...form, is_archived: e.target.checked })
                      }
                    />
                    <span className="text-sm">{t("archive")}</span>
                  </label>
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <Button onClick={handleSave}>{t("submit")}</Button>
                <Button
                  variant="outline"
                  onClick={() => setSelected(null)}
                >
                  {t("cancel")}
                </Button>
                <Button
                  variant="ghost"
                  className="ml-auto text-red-600 hover:text-red-700"
                  onClick={handleDelete}
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  {t("delete")}
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {t("pickCategory")}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Create dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {t("new")} — {t("categories")}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label>{t("slug")} *</Label>
              <Input
                value={createForm.slug}
                onChange={(e) =>
                  setCreateForm({ ...createForm, slug: e.target.value })
                }
                placeholder="e.g. martial_arts"
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label>{t("nameEn")} *</Label>
                <Input
                  value={createForm.name_en}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, name_en: e.target.value })
                  }
                />
              </div>
              <div className="grid gap-2">
                <Label>{t("nameZh")} *</Label>
                <Input
                  value={createForm.name_zh}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, name_zh: e.target.value })
                  }
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>{t("parent")}</Label>
              <Select
                value={createForm.parent_category_id || "__top__"}
                onValueChange={(v) =>
                  setCreateForm({
                    ...createForm,
                    parent_category_id: v === "__top__" ? "" : v,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__top__">
                    — {t("rootLevel")} —
                  </SelectItem>
                  {createParentCandidates.map((c) => (
                    <SelectItem key={c.category_id} value={c.category_id}>
                      {" ".repeat((c.depth - 1) * 2)}
                      {(lang === "zh" ? c.name_zh : c.name_en) + ` (${c.slug})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {t("depthLimitHint")}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              {t("cancel")}
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!createForm.slug || !createForm.name_en || !createForm.name_zh}
            >
              {t("submit")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

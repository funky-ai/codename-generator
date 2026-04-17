const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Category {
  category_id: string;
  slug: string;
  name_en: string;
  name_zh: string;
  parent_category_id: string | null;
  sort_order: number;
  is_archived: boolean;
  created_at: string;
  depth: number;
  children?: Category[] | null;
  codename_count?: number | null;
}

export interface CategoryInput {
  slug: string;
  name_en: string;
  name_zh: string;
  parent_category_id?: string | null;
  sort_order?: number;
}

export interface CategoryUpdate {
  slug?: string;
  name_en?: string;
  name_zh?: string;
  parent_category_id?: string | null;
  sort_order?: number;
  is_archived?: boolean;
}

export interface CategoryStat {
  category_id: string;
  slug: string;
  name_en: string;
  name_zh: string;
  depth: number;
  total: number;
  available: number;
  assigned: number;
}

export interface Codename {
  codename_id: string;
  name: string;
  name_en: string;
  name_zh: string;
  category_id: string;
  category_path: string[];
  brief: string;
  status: "available" | "assigned";
  added_at: string;
}

export interface CodenameInput {
  name: string;
  name_en: string;
  name_zh: string;
  category_id: string;
  brief: string;
}

export interface CodenameUpdate {
  name?: string;
  name_en?: string;
  name_zh?: string;
  category_id?: string;
  brief?: string;
}

export interface Assignment {
  assignment_id: string;
  codename_id: string;
  codename_name: string;
  description: string | null;
  assigned_by: string;
  assigned_at: string;
}

export type LogAction =
  | "added"
  | "assigned"
  | "updated"
  | "category_added"
  | "category_updated"
  | "category_archived"
  | "category_deleted";

export interface LogEntry {
  timestamp: string;
  action: LogAction;
  codename_id: string;
  operator: string;
  details: string | null;
}

export interface InventoryStats {
  total: number;
  available: number;
  assigned: number;
  by_category: CategoryStat[];
  low_stock_warning: boolean;
  warning_message: string | null;
}

export interface AddResult {
  added: number;
  codename_ids: string[];
  errors: string[];
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export const api = {
  // Stats + inventory queries (reads)
  getStats: () => request<InventoryStats>("/stats"),

  listCategories: (params?: {
    tree?: boolean;
    include_archived?: boolean;
    parent_category_id?: string | null;
  }) => {
    const qs = new URLSearchParams();
    if (params?.tree) qs.set("tree", "1");
    if (params?.include_archived) qs.set("include_archived", "1");
    if (params?.parent_category_id !== undefined && params.parent_category_id !== null) {
      qs.set("parent_category_id", params.parent_category_id);
    } else if (params?.parent_category_id === null) {
      // null → top-level only (API uses empty-string convention)
      qs.set("parent_category_id", "");
    }
    const q = qs.toString();
    return request<Category[]>(`/categories${q ? `?${q}` : ""}`);
  },

  getCategory: (categoryId: string) =>
    request<Category>(`/categories/${categoryId}`),

  getCodenames: (params?: {
    category_id?: string;
    include_descendants?: boolean;
    status?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params?.category_id) qs.set("category_id", params.category_id);
    if (params?.include_descendants === false) qs.set("include_descendants", "false");
    if (params?.status) qs.set("status", params.status);
    const q = qs.toString();
    return request<Codename[]>(`/codenames${q ? `?${q}` : ""}`);
  },

  searchCodenames: (q: string) =>
    request<Codename[]>(`/codenames/search?q=${encodeURIComponent(q)}`),

  drawRandom: (
    count = 3,
    params?: { category_id?: string; include_descendants?: boolean }
  ) => {
    const qs = new URLSearchParams({ count: String(count) });
    if (params?.category_id) qs.set("category_id", params.category_id);
    if (params?.include_descendants === false) qs.set("include_descendants", "false");
    return request<Codename[]>(`/codenames/random?${qs}`);
  },

  getAssignments: () => request<Assignment[]>("/assignments"),

  getLogs: (limit = 50, action?: LogAction) => {
    const qs = new URLSearchParams({ limit: String(limit) });
    if (action) qs.set("action", action);
    return request<LogEntry[]>(`/logs?${qs}`);
  },

  // Codename writes
  addCodenames: (codenames: CodenameInput[], operator = "web") =>
    request<AddResult>("/codenames", {
      method: "POST",
      body: JSON.stringify({ codenames, operator }),
    }),

  updateCodename: (
    codenameId: string,
    data: CodenameUpdate & { operator?: string }
  ) =>
    request<Codename>(`/codenames/${codenameId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  assignCodename: (
    codenameId: string,
    description?: string,
    assignedBy = "web"
  ) =>
    request<Assignment>(`/codenames/${codenameId}/assign`, {
      method: "POST",
      body: JSON.stringify({ description, assigned_by: assignedBy }),
    }),

  // Category writes
  createCategory: (input: CategoryInput, operator = "web") =>
    request<Category>("/categories", {
      method: "POST",
      body: JSON.stringify({ ...input, operator }),
    }),

  updateCategory: (
    categoryId: string,
    data: CategoryUpdate & { operator?: string }
  ) =>
    request<Category>(`/categories/${categoryId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteCategory: (categoryId: string, operator = "web") => {
    const qs = new URLSearchParams({ operator });
    return request<{ deleted: string }>(`/categories/${categoryId}?${qs}`, {
      method: "DELETE",
    });
  },
};

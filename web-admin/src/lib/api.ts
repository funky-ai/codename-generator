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

export interface Codename {
  codename_id: string;
  name: string;
  name_en: string;
  name_zh: string;
  theme: "person" | "animal";
  sub_theme: string | null;
  brief: string;
  status: "available" | "assigned";
  added_at: string;
}

export interface Assignment {
  assignment_id: string;
  codename_id: string;
  codename_name: string;
  description: string | null;
  assigned_by: string;
  assigned_at: string;
}

export interface LogEntry {
  timestamp: string;
  action: "added" | "assigned" | "updated";
  codename_id: string;
  operator: string;
  details: string | null;
}

export interface InventoryStats {
  total: number;
  available: number;
  assigned: number;
  by_theme: Record<string, number>;
  available_by_theme: Record<string, number>;
  low_stock_warning: boolean;
  warning_message: string | null;
}

export interface CodenameInput {
  name: string;
  name_en: string;
  name_zh: string;
  theme: "person" | "animal";
  sub_theme?: string | null;
  brief: string;
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
  getStats: () => request<InventoryStats>("/stats"),

  getCodenames: (params?: {
    theme?: string;
    status?: string;
    sub_theme?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params?.theme) qs.set("theme", params.theme);
    if (params?.status) qs.set("status", params.status);
    if (params?.sub_theme) qs.set("sub_theme", params.sub_theme);
    const q = qs.toString();
    return request<Codename[]>(`/codenames${q ? `?${q}` : ""}`);
  },

  searchCodenames: (q: string) =>
    request<Codename[]>(`/codenames/search?q=${encodeURIComponent(q)}`),

  drawRandom: (count = 3, theme?: string) => {
    const qs = new URLSearchParams({ count: String(count) });
    if (theme) qs.set("theme", theme);
    return request<Codename[]>(`/codenames/random?${qs}`);
  },

  addCodenames: (codenames: CodenameInput[], operator = "web") =>
    request<AddResult>("/codenames", {
      method: "POST",
      body: JSON.stringify({ codenames, operator }),
    }),

  updateCodename: (
    codenameId: string,
    data: Partial<CodenameInput> & { operator?: string }
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

  getAssignments: () => request<Assignment[]>("/assignments"),

  getLogs: (limit = 50, action?: string) => {
    const qs = new URLSearchParams({ limit: String(limit) });
    if (action) qs.set("action", action);
    return request<LogEntry[]>(`/logs?${qs}`);
  },
};

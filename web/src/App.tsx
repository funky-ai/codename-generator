import { useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  LayoutDashboard,
  Database,
  Plus,
  Shuffle,
  Link,
  FileText,
  Menu,
  X,
  Languages,
} from "lucide-react";
import { useLang } from "@/hooks/use-lang";
import DashboardPage from "@/pages/Dashboard";
import InventoryPage from "@/pages/Inventory";
import AddPage from "@/pages/Add";
import DrawPage from "@/pages/Draw";
import AssignmentsPage from "@/pages/Assignments";
import LogsPage from "@/pages/Logs";

type Page = "dashboard" | "inventory" | "add" | "draw" | "assignments" | "logs";

const navItems: { page: Page; icon: typeof LayoutDashboard; labelKey: "dashboard" | "inventory" | "add" | "draw" | "assignments" | "logs" }[] = [
  { page: "dashboard", icon: LayoutDashboard, labelKey: "dashboard" },
  { page: "inventory", icon: Database, labelKey: "inventory" },
  { page: "add", icon: Plus, labelKey: "add" },
  { page: "draw", icon: Shuffle, labelKey: "draw" },
  { page: "assignments", icon: Link, labelKey: "assignments" },
  { page: "logs", icon: FileText, labelKey: "logs" },
];

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [menuOpen, setMenuOpen] = useState(false);
  const { t, toggle } = useLang();

  const navigate = (p: Page) => {
    setPage(p);
    setMenuOpen(false);
  };

  const renderPage = () => {
    switch (page) {
      case "dashboard":
        return <DashboardPage onNavigate={navigate} />;
      case "inventory":
        return <InventoryPage />;
      case "add":
        return <AddPage />;
      case "draw":
        return <DrawPage />;
      case "assignments":
        return <AssignmentsPage />;
      case "logs":
        return <LogsPage />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-14 items-center px-4">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden mr-2"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>

          <h1 className="text-lg font-semibold mr-6">{t("appName")}</h1>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map(({ page: p, icon: Icon, labelKey }) => (
              <Button
                key={p}
                variant={page === p ? "secondary" : "ghost"}
                size="sm"
                onClick={() => navigate(p)}
                className="gap-1.5"
              >
                <Icon className="h-4 w-4" />
                {t(labelKey)}
              </Button>
            ))}
          </nav>

          <div className="ml-auto">
            <Button variant="ghost" size="sm" onClick={toggle} className="gap-1.5">
              <Languages className="h-4 w-4" />
              {t("language")}
            </Button>
          </div>
        </div>

        {/* Mobile nav */}
        {menuOpen && (
          <div className="md:hidden border-t">
            <nav className="container mx-auto flex flex-col px-4 py-2 gap-1">
              {navItems.map(({ page: p, icon: Icon, labelKey }) => (
                <Button
                  key={p}
                  variant={page === p ? "secondary" : "ghost"}
                  size="sm"
                  onClick={() => navigate(p)}
                  className="justify-start gap-2"
                >
                  <Icon className="h-4 w-4" />
                  {t(labelKey)}
                </Button>
              ))}
            </nav>
            <Separator />
          </div>
        )}
      </header>

      {/* Main content */}
      <main className="container mx-auto px-4 py-6">{renderPage()}</main>

      <Toaster />
    </div>
  );
}

import { useState } from "react";
import { Toaster } from "@shared/components/ui/sonner";
import { Button } from "@shared/components/ui/button";
import { Separator } from "@shared/components/ui/separator";
import {
  Home,
  Database,
  Shuffle,
  Link,
  Menu,
  X,
  Languages,
} from "lucide-react";
import { useLang } from "@/lib/user-i18n";
import HomePage from "@/pages/Home";
import BrowsePage from "@/pages/Browse";
import DrawPage from "@/pages/Draw";
import AssignmentsPage from "@/pages/Assignments";

type Page = "home" | "browse" | "draw" | "assignments";

const navItems: {
  page: Page;
  icon: typeof Home;
  labelKey: "home" | "browse" | "draw" | "assignments";
}[] = [
  { page: "home", icon: Home, labelKey: "home" },
  { page: "browse", icon: Database, labelKey: "browse" },
  { page: "draw", icon: Shuffle, labelKey: "draw" },
  { page: "assignments", icon: Link, labelKey: "assignments" },
];

export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [menuOpen, setMenuOpen] = useState(false);
  const { t, toggle } = useLang();

  const navigate = (p: Page) => {
    setPage(p);
    setMenuOpen(false);
  };

  const renderPage = () => {
    switch (page) {
      case "home":
        return <HomePage onNavigate={navigate} />;
      case "browse":
        return <BrowsePage />;
      case "draw":
        return <DrawPage />;
      case "assignments":
        return <AssignmentsPage />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
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

          <div className="flex items-center gap-2 mr-6 shrink-0">
            <img src="/logo.svg" alt="Logo" className="h-6 shrink-0" />
            <h1 className="text-lg font-semibold whitespace-nowrap">{t("appName")}</h1>
          </div>

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

      <main className="container mx-auto px-4 py-6">{renderPage()}</main>

      <Toaster />
    </div>
  );
}

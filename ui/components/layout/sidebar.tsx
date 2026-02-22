"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/shared/ThemeToggle";
import { OrgSwitcher } from "@/components/organization";
import { useAuth } from "@/contexts/auth-context";
import { createClient } from "@/lib/supabase/client";
import type { User } from "@supabase/supabase-js";
import {
  LayoutDashboard,
  MessageSquare,
  AlertTriangle,
  TestTube2,
  ClipboardList,
  BarChart3,
  Users,
  Bot,
  FileText,
  Menu,
  X,
  LogOut,
} from "lucide-react";
import { Button } from "@/components/primitives/button";

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavigationSection {
  label: string;
  items: NavigationItem[];
}

export function Sidebar() {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const supabase = createClient();
  const { activeOrg } = useAuth();

  const navigationSections: NavigationSection[] = useMemo(
    () => [
      {
        label: "Dashboard",
        items: [{ name: "Dashboard", href: "/", icon: LayoutDashboard }],
      },
      {
        label: "Observability",
        items: [{ name: "Conversations", href: "/conversations", icon: MessageSquare }],
      },
      {
        label: "Simulations",
        items: [
          {
            name: "Test Suites",
            href: activeOrg ? `/orgs/${activeOrg.id}/test-suites` : "/test-suites",
            icon: TestTube2,
          },
          { name: "Test Scenarios", href: "/test-scenarios", icon: ClipboardList },
          { name: "Results", href: "/test-results", icon: BarChart3 },
          { name: "Personas", href: "/personas", icon: Users },
          {
            name: "Agents",
            href: activeOrg ? `/orgs/${activeOrg.id}/agents` : "/agents",
            icon: Bot,
          },
        ],
      },
      {
        label: "Analysis",
        items: [{ name: "Reports", href: "/reports", icon: FileText }],
      },
    ],
    [activeOrg?.id]
  );

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  };

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname?.startsWith(href);
  };

  const SidebarContent = () => (
    <>
      <div className="relative border-b border-sidebar-border p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <MessageSquare className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-sidebar-foreground">voiceobs</h1>
            <p className="text-xs text-sidebar-foreground/60">Voice Pipeline Testing</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-4 top-4 md:hidden"
          onClick={() => setIsMobileOpen(false)}
          aria-label="Close sidebar"
        >
          <X className="h-5 w-5" />
        </Button>
      </div>
      {/* Organization switcher */}
      <div className="border-b border-sidebar-border px-3 py-2">
        <OrgSwitcher />
      </div>
      <nav className="scrollbar-thin flex-1 overflow-y-auto p-4">
        {navigationSections.map((section, sectionIndex) => (
          <div key={section.label} className={sectionIndex > 0 ? "mt-6" : ""}>
            {section.label && (
              <p className="mb-2 px-3 text-xs font-medium uppercase tracking-wider text-sidebar-foreground/50">
                {section.label}
              </p>
            )}
            <div className="space-y-1">
              {section.items.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setIsMobileOpen(false)}
                    className={cn("nav-item", active && "nav-item-active")}
                  >
                    <item.icon className="h-5 w-5" />
                    <span className="text-sm font-medium">{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      {/* User section at bottom */}
      <div className="mt-auto border-t pt-4">
        {user ? (
          <div className="space-y-2">
            <div className="truncate px-3 text-sm text-muted-foreground">{user.email}</div>
            <Button variant="ghost" className="w-full justify-start" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </Button>
          </div>
        ) : null}
      </div>
      <div className="border-t border-sidebar-border p-4">
        <div className="flex items-center justify-center">
          <ThemeToggle />
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed left-4 top-4 z-50 md:hidden"
        onClick={() => setIsMobileOpen(true)}
        aria-label="Open sidebar"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-sidebar-border bg-sidebar transition-transform duration-300 md:relative md:z-auto md:translate-x-0",
          isMobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        <div className="relative flex h-full flex-col">
          <SidebarContent />
        </div>
      </aside>
    </>
  );
}

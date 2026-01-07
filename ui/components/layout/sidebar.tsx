"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/shared/ThemeToggle";
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
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavigationSection {
  label: string;
  items: NavigationItem[];
}

const navigationSections: NavigationSection[] = [
  {
    label: "Dashboard",
    items: [
      { name: "Dashboard", href: "/", icon: LayoutDashboard },
    ],
  },
  {
    label: "Observability",
    items: [
      { name: "Conversations", href: "/conversations", icon: MessageSquare },
    ],
  },
  {
    label: "Simulations",
    items: [
      { name: "Test Suites", href: "/test-suites", icon: TestTube2 },
      { name: "Test Scenarios", href: "/test-scenarios", icon: ClipboardList },
      { name: "Results", href: "/test-results", icon: BarChart3 },
      { name: "Personas", href: "/personas", icon: Users },
      { name: "Agents", href: "/agents", icon: Bot },
    ],
  },
  {
    label: "Analysis",
    items: [
      { name: "Reports", href: "/reports", icon: FileText },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname?.startsWith(href);
  };

  const SidebarContent = () => (
    <>
      <div className="p-6 border-b border-sidebar-border relative">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-semibold text-sidebar-foreground text-lg">voiceobs</h1>
            <p className="text-xs text-sidebar-foreground/60">Voice Pipeline Testing</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-4 right-4 md:hidden"
          onClick={() => setIsMobileOpen(false)}
          aria-label="Close sidebar"
        >
          <X className="h-5 w-5" />
        </Button>
      </div>
      <nav className="flex-1 p-4 overflow-y-auto scrollbar-thin">
        {navigationSections.map((section, sectionIndex) => (
          <div key={section.label} className={sectionIndex > 0 ? "mt-6" : ""}>
            {section.label && (
              <p className="px-3 mb-2 text-xs font-medium text-sidebar-foreground/50 uppercase tracking-wider">
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
                    className={cn(
                      "nav-item",
                      active && "nav-item-active"
                    )}
                  >
                    <item.icon className="w-5 h-5" />
                    <span className="text-sm font-medium">{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <div className="p-4 border-t border-sidebar-border">
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
          "fixed left-0 top-0 z-40 w-64 bg-sidebar border-r border-sidebar-border flex flex-col h-screen transition-transform duration-300 md:relative md:z-auto md:translate-x-0",
          isMobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        <div className="flex h-full flex-col relative">
          <SidebarContent />
        </div>
      </aside>
    </>
  );
}

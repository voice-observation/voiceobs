"use client";

import { usePathname } from "next/navigation";

// Map routes to page titles
const routeTitles: Record<string, string> = {
  "/": "Dashboard",
  "/conversations": "Conversations",
  "/test-suites": "Test Suites",
  "/test-scenarios": "Test Scenarios",
  "/test-results": "Test Results",
  "/personas": "Personas",
  "/reports": "Reports",
  "/agents": "Agents",
};

export function Header() {
  const pathname = usePathname();

  // Get the current page title based on the pathname
  const getPageTitle = () => {
    // Check for exact matches first
    if (routeTitles[pathname]) {
      return routeTitles[pathname];
    }

    // Check for routes that start with a known path
    for (const [route, title] of Object.entries(routeTitles)) {
      if (route !== "/" && pathname?.startsWith(route)) {
        return title;
      }
    }

    return "Voice AI Observability";
  };

  // Don't show header title for personas page (it has its own title)
  const shouldShowTitle = pathname !== "/personas";

  return (
    <header className="flex h-16 items-center border-b border-border bg-background px-4 md:px-6">
      {shouldShowTitle && (
        <div className="ml-12 flex items-center gap-2 md:ml-0">
          <h2 className="text-lg font-semibold">{getPageTitle()}</h2>
        </div>
      )}
    </header>
  );
}

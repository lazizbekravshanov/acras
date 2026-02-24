"use client";

import { usePathname } from "next/navigation";
import { Search } from "lucide-react";
import NotificationBell from "./NotificationBell";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useIncidents } from "@/hooks/useIncidents";
import { cn } from "@/lib/utils";

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/incidents": "Incidents",
  "/cameras": "Cameras",
  "/analytics": "Analytics",
  "/reports": "Reports",
  "/settings": "Settings",
};

function getPageTitle(pathname: string): string {
  // Check exact match first
  if (pageTitles[pathname]) return pageTitles[pathname];

  // Check prefix match for nested routes
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length >= 1) {
    const base = `/${segments[0]}`;
    if (pageTitles[base]) {
      if (segments.length === 1) return pageTitles[base];
      return `${pageTitles[base]} Detail`;
    }
  }

  return "ACRAS";
}

export default function Header() {
  const pathname = usePathname();
  const { isConnected } = useWebSocket();
  const { incidents } = useIncidents({ autoRefresh: true });
  const title = getPageTitle(pathname);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-surface-border bg-surface-card/80 backdrop-blur-sm px-6">
      {/* Page Title */}
      <h1 className="text-xl font-semibold text-gray-100">{title}</h1>

      {/* Right side controls */}
      <div className="flex items-center gap-4">
        {/* Search (cosmetic) */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search incidents, cameras..."
            className="h-9 w-64 rounded-lg border border-surface-border bg-surface-elevated pl-9 pr-4 text-sm text-gray-100 placeholder-gray-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            readOnly
          />
        </div>

        {/* System Status */}
        <div className="flex items-center gap-2 rounded-lg border border-surface-border px-3 py-1.5">
          <span
            className={cn(
              "h-2.5 w-2.5 rounded-full",
              isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"
            )}
          />
          <span className="text-xs font-medium text-gray-400">
            {isConnected ? "System Online" : "Connecting..."}
          </span>
        </div>

        {/* Notification Bell */}
        <NotificationBell incidents={incidents} />
      </div>
    </header>
  );
}

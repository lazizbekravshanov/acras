"use client";

import { useState, useRef, useEffect } from "react";
import { Bell } from "lucide-react";
import { cn, formatRelativeTime, severityColor } from "@/lib/utils";
import type { Incident } from "@/lib/types";

interface NotificationBellProps {
  incidents: Incident[];
}

export default function NotificationBell({
  incidents,
}: NotificationBellProps) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Active (non-resolved, non-false-positive) incidents
  const activeIncidents = incidents.filter(
    (i) => i.status !== "resolved" && i.status !== "false_positive"
  );
  const count = activeIncidents.length;

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="relative rounded-lg p-2 text-gray-400 hover:bg-surface-elevated hover:text-gray-100 transition-colors"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {count > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 rounded-lg border border-surface-border bg-surface-card shadow-xl z-50">
          <div className="border-b border-surface-border px-4 py-3">
            <h3 className="text-sm font-semibold text-gray-100">
              Active Incidents ({count})
            </h3>
          </div>

          <div className="max-h-80 overflow-y-auto">
            {activeIncidents.length === 0 ? (
              <div className="px-4 py-6 text-center text-sm text-gray-500">
                No active incidents
              </div>
            ) : (
              activeIncidents.slice(0, 10).map((incident) => {
                const colors = severityColor(incident.severity);
                return (
                  <a
                    key={incident.id}
                    href={`/incidents/${incident.id}`}
                    className="flex items-start gap-3 border-b border-surface-border px-4 py-3 hover:bg-surface-elevated transition-colors last:border-0"
                    onClick={() => setOpen(false)}
                  >
                    <span
                      className={cn(
                        "mt-1 h-2.5 w-2.5 shrink-0 rounded-full",
                        colors.dot
                      )}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-100 truncate">
                        {incident.incident_type.replace(/_/g, " ")} on{" "}
                        {incident.interstate}
                      </p>
                      <p className="text-xs text-gray-500">
                        {incident.severity} &middot;{" "}
                        {formatRelativeTime(incident.detected_at)}
                      </p>
                    </div>
                  </a>
                );
              })
            )}
          </div>

          {count > 10 && (
            <div className="border-t border-surface-border px-4 py-2">
              <a
                href="/incidents"
                className="text-xs text-accent hover:text-accent-hover"
                onClick={() => setOpen(false)}
              >
                View all incidents
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

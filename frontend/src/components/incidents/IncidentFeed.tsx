"use client";

import { AlertTriangle } from "lucide-react";
import type { Incident } from "@/lib/types";
import IncidentCard from "./IncidentCard";

interface IncidentFeedProps {
  incidents: Incident[];
  loading?: boolean;
  maxItems?: number;
}

export default function IncidentFeed({
  incidents,
  loading = false,
  maxItems,
}: IncidentFeedProps) {
  const displayItems = maxItems
    ? incidents.slice(0, maxItems)
    : incidents;

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-lg bg-surface-card"
          />
        ))}
      </div>
    );
  }

  if (incidents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <AlertTriangle className="h-10 w-10 mb-3 opacity-50" />
        <p className="text-sm font-medium">No incidents</p>
        <p className="text-xs mt-1">All clear for now.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 overflow-y-auto pr-1">
      {displayItems.map((incident) => (
        <IncidentCard key={incident.id} incident={incident} />
      ))}
    </div>
  );
}

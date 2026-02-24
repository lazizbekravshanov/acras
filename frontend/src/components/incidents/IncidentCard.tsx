"use client";

import Link from "next/link";
import { Clock, Car, MapPin, Percent } from "lucide-react";
import type { Incident } from "@/lib/types";
import SeverityBadge from "./SeverityBadge";
import { cn, formatRelativeTime, statusColor, severityColor } from "@/lib/utils";

interface IncidentCardProps {
  incident: Incident;
}

export default function IncidentCard({ incident }: IncidentCardProps) {
  const sevColors = severityColor(incident.severity);
  const statColors = statusColor(incident.status);

  return (
    <Link href={`/incidents/${incident.id}`}>
      <div
        className={cn(
          "rounded-lg border-l-4 bg-surface-card p-4 transition-all hover:bg-surface-elevated cursor-pointer",
          sevColors.border
        )}
      >
        {/* Top row: severity badge + status */}
        <div className="flex items-center justify-between mb-2">
          <SeverityBadge severity={incident.severity} />
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium capitalize",
              statColors.bg,
              statColors.text
            )}
          >
            <span
              className={cn("h-1.5 w-1.5 rounded-full", statColors.dot)}
            />
            {incident.status.replace(/_/g, " ")}
          </span>
        </div>

        {/* Incident type */}
        <h3 className="text-sm font-semibold text-gray-100 mb-2 capitalize">
          {incident.incident_type.replace(/_/g, " ")}
        </h3>

        {/* Details row */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <MapPin className="h-3.5 w-3.5" />
            {incident.interstate}
            {incident.direction ? ` ${incident.direction}` : ""}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {formatRelativeTime(incident.detected_at)}
          </span>
          <span className="flex items-center gap-1">
            <Percent className="h-3.5 w-3.5" />
            {(incident.confidence * 100).toFixed(0)}%
          </span>
          {incident.vehicle_count !== null && (
            <span className="flex items-center gap-1">
              <Car className="h-3.5 w-3.5" />
              {incident.vehicle_count} vehicle
              {incident.vehicle_count !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

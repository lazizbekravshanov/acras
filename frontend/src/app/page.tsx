"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  Camera,
  AlertTriangle,
  Calendar,
  CalendarDays,
} from "lucide-react";
import { api } from "@/lib/api";
import type { SummaryStats, Incident, Camera as CameraType } from "@/lib/types";
import { useIncidents } from "@/hooks/useIncidents";
import { useCameras } from "@/hooks/useCameras";
import IncidentFeed from "@/components/incidents/IncidentFeed";

const LiveMap = dynamic(() => import("@/components/map/LiveMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center rounded-lg bg-surface-card">
      <div className="text-sm text-gray-500">Loading map...</div>
    </div>
  ),
});

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: string;
}

function StatCard({ label, value, icon, trend }: StatCardProps) {
  return (
    <div className="rounded-lg border border-surface-border bg-surface-card p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          {label}
        </span>
        <div className="rounded-lg bg-surface-elevated p-2">{icon}</div>
      </div>
      <p className="text-2xl font-bold text-gray-100">{value}</p>
      {trend && (
        <p className="text-xs text-gray-500 mt-1">{trend}</p>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const { incidents, loading: incidentsLoading } = useIncidents({
    pageSize: 20,
  });
  const { cameras } = useCameras();

  useEffect(() => {
    async function fetchSummary() {
      try {
        const data = await api.getSummary();
        setSummary(data);
      } catch {
        // API may not be available; use fallback zeros
        setSummary({
          active_cameras: 0,
          active_incidents: 0,
          incidents_today: 0,
          incidents_this_week: 0,
          avg_detection_time_seconds: null,
          avg_resolution_time_minutes: null,
          false_positive_rate: null,
          top_severity: null,
        });
      } finally {
        setSummaryLoading(false);
      }
    }
    fetchSummary();
    const interval = setInterval(fetchSummary, 30000);
    return () => clearInterval(interval);
  }, []);

  // Active (non-resolved) incidents for the map
  const activeIncidents = incidents.filter(
    (i) => i.status !== "resolved" && i.status !== "false_positive"
  );

  return (
    <div className="space-y-6">
      {/* Stat Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Cameras"
          value={
            summaryLoading ? "..." : (summary?.active_cameras ?? 0)
          }
          icon={<Camera className="h-5 w-5 text-green-400" />}
        />
        <StatCard
          label="Active Incidents"
          value={
            summaryLoading ? "..." : (summary?.active_incidents ?? 0)
          }
          icon={<AlertTriangle className="h-5 w-5 text-red-400" />}
        />
        <StatCard
          label="Incidents Today"
          value={
            summaryLoading ? "..." : (summary?.incidents_today ?? 0)
          }
          icon={<Calendar className="h-5 w-5 text-amber-400" />}
        />
        <StatCard
          label="This Week"
          value={
            summaryLoading
              ? "..."
              : (summary?.incidents_this_week ?? 0)
          }
          icon={<CalendarDays className="h-5 w-5 text-blue-400" />}
        />
      </div>

      {/* Map + Feed Row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6" style={{ minHeight: "500px" }}>
        {/* Live Map (60%) */}
        <div className="lg:col-span-3 rounded-lg border border-surface-border overflow-hidden" style={{ minHeight: "500px" }}>
          <LiveMap
            cameras={cameras}
            incidents={activeIncidents}
          />
        </div>

        {/* Incident Feed (40%) */}
        <div className="lg:col-span-2 flex flex-col rounded-lg border border-surface-border bg-surface-card">
          <div className="border-b border-surface-border px-4 py-3">
            <h2 className="text-sm font-semibold text-gray-100">
              Recent Incidents
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto p-3" style={{ maxHeight: "460px" }}>
            <IncidentFeed
              incidents={incidents}
              loading={incidentsLoading}
              maxItems={15}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import {
  ArrowLeft,
  MapPin,
  Clock,
  Car,
  Percent,
  Cloud,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Incident, Report } from "@/lib/types";
import SeverityBadge from "@/components/incidents/SeverityBadge";
import ReportViewer from "@/components/reports/ReportViewer";
import {
  cn,
  formatDate,
  formatRelativeTime,
  statusColor,
  severityColor,
} from "@/lib/utils";

const LiveMap = dynamic(() => import("@/components/map/LiveMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-64 items-center justify-center rounded-lg bg-surface-card">
      <span className="text-sm text-gray-500">Loading map...</span>
    </div>
  ),
});

interface TimelineEntry {
  label: string;
  time: string | null;
  active: boolean;
}

export default function IncidentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [incident, setIncident] = useState<Incident | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const incidentData = await api.getIncident(id);
        setIncident(incidentData);

        // Try to fetch associated report
        try {
          const reports = await api.getReports({ incident_id: id });
          if (reports.items.length > 0) {
            setReport(reports.items[0]);
          }
        } catch {
          // No report available, that is fine
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch incident"
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [id]);

  async function handleStatusChange(newStatus: string) {
    if (!incident || updating) return;
    setUpdating(true);
    try {
      const updated = await api.updateIncident(incident.id, {
        status: newStatus as Incident["status"],
      });
      setIncident(updated);
    } catch {
      // Failed to update
    } finally {
      setUpdating(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-surface-card" />
        <div className="h-64 animate-pulse rounded-lg bg-surface-card" />
        <div className="h-48 animate-pulse rounded-lg bg-surface-card" />
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6 text-center">
        <p className="text-red-400">{error || "Incident not found"}</p>
        <button
          onClick={() => router.push("/incidents")}
          className="mt-3 text-sm text-accent hover:text-accent-hover"
        >
          Back to Incidents
        </button>
      </div>
    );
  }

  const sevColors = severityColor(incident.severity);
  const statCol = statusColor(incident.status);

  const timeline: TimelineEntry[] = [
    { label: "Detected", time: incident.detected_at, active: true },
    {
      label: "Confirmed",
      time: incident.confirmed_at,
      active: !!incident.confirmed_at,
    },
    {
      label: "Responding",
      time: incident.status === "responding" ? incident.updated_at : null,
      active: ["responding", "clearing", "resolved"].includes(incident.status),
    },
    {
      label: "Clearing",
      time: incident.status === "clearing" ? incident.updated_at : null,
      active: ["clearing", "resolved"].includes(incident.status),
    },
    {
      label: "Resolved",
      time: incident.resolved_at,
      active: incident.status === "resolved",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Back Button + Title */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/incidents")}
          className="rounded-lg border border-surface-border p-2 text-gray-400 hover:bg-surface-elevated hover:text-gray-100 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-100 capitalize">
            {incident.incident_type.replace(/_/g, " ")}
          </h1>
          <p className="text-sm text-gray-500">ID: {incident.id}</p>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Left: Details */}
        <div className="md:col-span-2 space-y-4">
          {/* Overview Card */}
          <div className="rounded-lg border border-surface-border bg-surface-card p-5">
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <SeverityBadge severity={incident.severity} />
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
                  statCol.bg,
                  statCol.text
                )}
              >
                <span className={cn("h-1.5 w-1.5 rounded-full", statCol.dot)} />
                {incident.status.replace(/_/g, " ")}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-gray-500 mt-0.5" />
                <div>
                  <p className="text-xs text-gray-500">Location</p>
                  <p className="text-sm text-gray-100">
                    {incident.interstate}
                    {incident.direction ? ` ${incident.direction}` : ""}
                  </p>
                  {incident.lane_impact && (
                    <p className="text-xs text-gray-400">
                      Lane: {incident.lane_impact}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Clock className="h-4 w-4 text-gray-500 mt-0.5" />
                <div>
                  <p className="text-xs text-gray-500">Detected</p>
                  <p className="text-sm text-gray-100">
                    {formatRelativeTime(incident.detected_at)}
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatDate(incident.detected_at)}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Percent className="h-4 w-4 text-gray-500 mt-0.5" />
                <div>
                  <p className="text-xs text-gray-500">Confidence</p>
                  <p className="text-sm text-gray-100">
                    {(incident.confidence * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-400">
                    Score: {incident.severity_score.toFixed(2)}
                  </p>
                </div>
              </div>

              {incident.vehicle_count !== null && (
                <div className="flex items-start gap-2">
                  <Car className="h-4 w-4 text-gray-500 mt-0.5" />
                  <div>
                    <p className="text-xs text-gray-500">Vehicles</p>
                    <p className="text-sm text-gray-100">
                      {incident.vehicle_count}
                    </p>
                  </div>
                </div>
              )}

              {incident.weather_conditions && (
                <div className="flex items-start gap-2">
                  <Cloud className="h-4 w-4 text-gray-500 mt-0.5" />
                  <div>
                    <p className="text-xs text-gray-500">Weather</p>
                    <p className="text-sm text-gray-100">
                      {(incident.weather_conditions as Record<string, unknown>)
                        .condition
                        ? String(
                            (
                              incident.weather_conditions as Record<
                                string,
                                unknown
                              >
                            ).condition
                          )
                        : "Available"}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Status Update Actions */}
          <div className="rounded-lg border border-surface-border bg-surface-card p-5">
            <h3 className="text-sm font-semibold text-gray-100 mb-3">
              Update Status
            </h3>
            <div className="flex flex-wrap gap-2">
              {incident.status !== "confirmed" &&
                incident.status === "detected" && (
                  <button
                    onClick={() => handleStatusChange("confirmed")}
                    disabled={updating}
                    className="flex items-center gap-1.5 rounded-lg bg-orange-500/20 px-3 py-1.5 text-xs font-medium text-orange-400 hover:bg-orange-500/30 transition-colors disabled:opacity-50"
                  >
                    <CheckCircle className="h-3.5 w-3.5" />
                    Confirm
                  </button>
                )}
              {["detected", "confirmed"].includes(incident.status) && (
                <button
                  onClick={() => handleStatusChange("responding")}
                  disabled={updating}
                  className="flex items-center gap-1.5 rounded-lg bg-blue-500/20 px-3 py-1.5 text-xs font-medium text-blue-400 hover:bg-blue-500/30 transition-colors disabled:opacity-50"
                >
                  <CheckCircle className="h-3.5 w-3.5" />
                  Mark Responding
                </button>
              )}
              {["responding"].includes(incident.status) && (
                <button
                  onClick={() => handleStatusChange("clearing")}
                  disabled={updating}
                  className="flex items-center gap-1.5 rounded-lg bg-indigo-500/20 px-3 py-1.5 text-xs font-medium text-indigo-400 hover:bg-indigo-500/30 transition-colors disabled:opacity-50"
                >
                  <CheckCircle className="h-3.5 w-3.5" />
                  Mark Clearing
                </button>
              )}
              {incident.status !== "resolved" &&
                incident.status !== "false_positive" && (
                  <>
                    <button
                      onClick={() => handleStatusChange("resolved")}
                      disabled={updating}
                      className="flex items-center gap-1.5 rounded-lg bg-green-500/20 px-3 py-1.5 text-xs font-medium text-green-400 hover:bg-green-500/30 transition-colors disabled:opacity-50"
                    >
                      <CheckCircle className="h-3.5 w-3.5" />
                      Resolve
                    </button>
                    <button
                      onClick={() => handleStatusChange("false_positive")}
                      disabled={updating}
                      className="flex items-center gap-1.5 rounded-lg bg-gray-500/20 px-3 py-1.5 text-xs font-medium text-gray-400 hover:bg-gray-500/30 transition-colors disabled:opacity-50"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                      False Positive
                    </button>
                  </>
                )}
            </div>
          </div>

          {/* Timeline */}
          <div className="rounded-lg border border-surface-border bg-surface-card p-5">
            <h3 className="text-sm font-semibold text-gray-100 mb-4">
              Timeline
            </h3>
            <div className="flex items-center gap-0">
              {timeline.map((entry, i) => (
                <div key={entry.label} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={cn(
                        "h-3 w-3 rounded-full border-2",
                        entry.active
                          ? `${sevColors.border} ${sevColors.dot}`
                          : "border-gray-600 bg-surface-elevated"
                      )}
                    />
                    <p
                      className={cn(
                        "text-[10px] mt-1.5 font-medium",
                        entry.active ? "text-gray-100" : "text-gray-600"
                      )}
                    >
                      {entry.label}
                    </p>
                    {entry.time && (
                      <p className="text-[9px] text-gray-500">
                        {formatRelativeTime(entry.time)}
                      </p>
                    )}
                  </div>
                  {i < timeline.length - 1 && (
                    <div
                      className={cn(
                        "h-0.5 w-12 sm:w-20 mx-1",
                        entry.active && timeline[i + 1].active
                          ? sevColors.dot
                          : "bg-gray-700"
                      )}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Report (if available) */}
          {report && (
            <div>
              <h3 className="text-sm font-semibold text-gray-100 mb-3">
                Generated Report
              </h3>
              <ReportViewer report={report} />
            </div>
          )}
        </div>

        {/* Right: Map */}
        <div className="space-y-4">
          <div
            className="rounded-lg border border-surface-border overflow-hidden"
            style={{ height: "300px" }}
          >
            <LiveMap
              incidents={[incident]}
              center={[incident.latitude, incident.longitude]}
              zoom={12}
            />
          </div>

          {/* Coordinates */}
          <div className="rounded-lg border border-surface-border bg-surface-card p-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Coordinates
            </h4>
            <p className="text-sm text-gray-300 font-mono">
              {incident.latitude.toFixed(6)}, {incident.longitude.toFixed(6)}
            </p>
          </div>

          {/* Camera Link */}
          <div className="rounded-lg border border-surface-border bg-surface-card p-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Source Camera
            </h4>
            <a
              href={`/cameras/${incident.camera_id}`}
              className="text-sm text-accent hover:text-accent-hover"
            >
              View Camera
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

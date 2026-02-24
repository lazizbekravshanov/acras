"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import {
  ArrowLeft,
  Video,
  MapPin,
  Wifi,
  Monitor,
  Building2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Camera, Incident } from "@/lib/types";
import CameraStatus from "@/components/cameras/CameraStatus";
import IncidentFeed from "@/components/incidents/IncidentFeed";
import { formatDate, formatRelativeTime } from "@/lib/utils";

const LiveMap = dynamic(() => import("@/components/map/LiveMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-48 items-center justify-center rounded-lg bg-surface-card">
      <span className="text-sm text-gray-500">Loading map...</span>
    </div>
  ),
});

export default function CameraDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [camera, setCamera] = useState<Camera | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const cameraData = await api.getCamera(id);
        setCamera(cameraData);

        // Fetch incidents for this camera
        try {
          const incidentData = await api.getIncidents({
            camera_id: id,
            page_size: 20,
          });
          setIncidents(incidentData.items);
        } catch {
          // No incidents, that is fine
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch camera"
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-surface-card" />
        <div className="h-64 animate-pulse rounded-lg bg-surface-card" />
      </div>
    );
  }

  if (error || !camera) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6 text-center">
        <p className="text-red-400">{error || "Camera not found"}</p>
        <button
          onClick={() => router.push("/cameras")}
          className="mt-3 text-sm text-accent hover:text-accent-hover"
        >
          Back to Cameras
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/cameras")}
          className="rounded-lg border border-surface-border p-2 text-gray-400 hover:bg-surface-elevated hover:text-gray-100 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-100">{camera.name}</h1>
            <CameraStatus status={camera.status} />
          </div>
          <p className="text-sm text-gray-500">ID: {camera.id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Stream + Details */}
        <div className="lg:col-span-2 space-y-4">
          {/* Stream Placeholder */}
          <div className="rounded-lg border border-surface-border bg-surface-card overflow-hidden">
            <div className="aspect-video flex flex-col items-center justify-center bg-surface-elevated relative">
              <Video className="h-16 w-16 text-gray-700 mb-3" />
              <p className="text-sm text-gray-500 font-medium">
                {camera.stream_type.toUpperCase()} Stream
              </p>
              <p className="text-xs text-gray-600 mt-1">{camera.stream_url}</p>

              {/* FPS badge */}
              {camera.fps_actual !== null && camera.fps_actual > 0 && (
                <div className="absolute top-3 right-3 flex items-center gap-1 rounded bg-black/60 px-2 py-1 text-xs font-mono text-green-400">
                  <Wifi className="h-3.5 w-3.5" />
                  {camera.fps_actual.toFixed(0)} FPS
                </div>
              )}
            </div>
          </div>

          {/* Camera Info */}
          <div className="rounded-lg border border-surface-border bg-surface-card p-5">
            <h3 className="text-sm font-semibold text-gray-100 mb-4">
              Camera Information
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-gray-500 mt-0.5" />
                <div>
                  <p className="text-xs text-gray-500">Location</p>
                  <p className="text-sm text-gray-100">
                    {camera.interstate}
                    {camera.direction ? ` ${camera.direction}` : ""}
                  </p>
                  <p className="text-xs text-gray-400">
                    {camera.state_code}
                    {camera.mile_marker !== null
                      ? ` / MM ${camera.mile_marker}`
                      : ""}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Monitor className="h-4 w-4 text-gray-500 mt-0.5" />
                <div>
                  <p className="text-xs text-gray-500">Resolution</p>
                  <p className="text-sm text-gray-100">
                    {camera.resolution_width && camera.resolution_height
                      ? `${camera.resolution_width}x${camera.resolution_height}`
                      : "Unknown"}
                  </p>
                </div>
              </div>

              {camera.source_agency && (
                <div className="flex items-start gap-2">
                  <Building2 className="h-4 w-4 text-gray-500 mt-0.5" />
                  <div>
                    <p className="text-xs text-gray-500">Agency</p>
                    <p className="text-sm text-gray-100">
                      {camera.source_agency}
                    </p>
                  </div>
                </div>
              )}

              <div>
                <p className="text-xs text-gray-500">Last Frame</p>
                <p className="text-sm text-gray-100">
                  {camera.last_frame_at
                    ? formatRelativeTime(camera.last_frame_at)
                    : "N/A"}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-500">Created</p>
                <p className="text-sm text-gray-100">
                  {formatDate(camera.created_at)}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-500">Coordinates</p>
                <p className="text-sm text-gray-300 font-mono">
                  {camera.latitude.toFixed(4)}, {camera.longitude.toFixed(4)}
                </p>
              </div>
            </div>

            {camera.description && (
              <div className="mt-4 pt-4 border-t border-surface-border">
                <p className="text-xs text-gray-500 mb-1">Description</p>
                <p className="text-sm text-gray-300">{camera.description}</p>
              </div>
            )}
          </div>

          {/* Incident History */}
          <div className="rounded-lg border border-surface-border bg-surface-card">
            <div className="border-b border-surface-border px-5 py-3">
              <h3 className="text-sm font-semibold text-gray-100">
                Incident History ({incidents.length})
              </h3>
            </div>
            <div className="p-3 max-h-96 overflow-y-auto">
              <IncidentFeed incidents={incidents} />
            </div>
          </div>
        </div>

        {/* Right: Map */}
        <div className="space-y-4">
          <div
            className="rounded-lg border border-surface-border overflow-hidden"
            style={{ height: "250px" }}
          >
            <LiveMap
              cameras={[camera]}
              center={[camera.latitude, camera.longitude]}
              zoom={13}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

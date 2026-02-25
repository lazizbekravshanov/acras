"use client";

import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import type { Camera, Incident, HeatmapPoint } from "@/lib/types";
import CameraMarker from "./CameraMarker";
import HeatmapLayer from "./HeatmapLayer";
import { severityColor, formatRelativeTime } from "@/lib/utils";

// Fix Leaflet default marker icons in Next.js
import "leaflet/dist/leaflet.css";

// Override default icon paths
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface LiveMapProps {
  cameras?: Camera[];
  incidents?: Incident[];
  heatmapPoints?: HeatmapPoint[];
  showHeatmap?: boolean;
  center?: [number, number];
  zoom?: number;
  className?: string;
}

function incidentIcon(severity: string): L.DivIcon {
  const colorMap: Record<string, string> = {
    minor: "#3b82f6",
    moderate: "#f59e0b",
    severe: "#f97316",
    critical: "#ef4444",
  };
  const color = colorMap[severity] || "#6b7280";

  return L.divIcon({
    className: "custom-incident-marker",
    html: `<div style="
      width: 20px;
      height: 20px;
      background-color: ${color};
      border: 2px solid white;
      border-radius: 4px;
      transform: rotate(45deg);
      box-shadow: 0 0 10px ${color}aa;
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    popupAnchor: [0, -14],
  });
}

/** Sub-component to re-center map when center prop changes. */
function MapCenterUpdater({
  center,
  zoom,
}: {
  center: [number, number];
  zoom: number;
}) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [map, center, zoom]);
  return null;
}

export default function LiveMap({
  cameras = [],
  incidents = [],
  heatmapPoints = [],
  showHeatmap = false,
  center = [39.8, -98.5],
  zoom = 4,
  className = "",
}: LiveMapProps) {
  return (
    <MapContainer
      center={center}
      zoom={zoom}
      className={`h-full w-full rounded-lg ${className}`}
      style={{ minHeight: "300px" }}
      zoomControl={true}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />

      <MapCenterUpdater center={center} zoom={zoom} />

      {/* Camera markers */}
      {cameras.map((camera) => (
        <CameraMarker key={camera.id} camera={camera} />
      ))}

      {/* Incident markers */}
      {incidents.map((incident) => (
        <Marker
          key={incident.id}
          position={[incident.latitude, incident.longitude]}
          icon={incidentIcon(incident.severity)}
        >
          <Popup>
            <div className="min-w-[200px]">
              <p className="font-semibold text-sm mb-1">
                {incident.incident_type.replace(/_/g, " ").toUpperCase()}
              </p>
              <div className="space-y-0.5 text-xs">
                <p>
                  <span className="text-gray-400">Severity: </span>
                  <span
                    className={severityColor(incident.severity).text}
                  >
                    {incident.severity}
                  </span>
                </p>
                <p>
                  <span className="text-gray-400">Location: </span>
                  {incident.interstate}
                  {incident.direction
                    ? ` ${incident.direction}`
                    : ""}
                </p>
                <p>
                  <span className="text-gray-400">Status: </span>
                  {incident.status}
                </p>
                <p>
                  <span className="text-gray-400">Confidence: </span>
                  {(incident.confidence * 100).toFixed(0)}%
                </p>
                <p>
                  <span className="text-gray-400">Detected: </span>
                  {formatRelativeTime(incident.detected_at)}
                </p>
                {incident.vehicle_count !== null && (
                  <p>
                    <span className="text-gray-400">Vehicles: </span>
                    {incident.vehicle_count}
                  </p>
                )}
              </div>
              <a
                href={`/incidents/${incident.id}`}
                className="mt-2 inline-block text-xs text-accent hover:text-accent-hover"
              >
                View details
              </a>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Heatmap overlay */}
      {showHeatmap && <HeatmapLayer points={heatmapPoints} />}
    </MapContainer>
  );
}

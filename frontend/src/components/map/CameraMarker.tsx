"use client";

import { Marker, Popup } from "react-leaflet";
import L from "leaflet";
import type { Camera } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";

interface CameraMarkerProps {
  camera: Camera;
}

function getMarkerIcon(status: string): L.DivIcon {
  let color: string;
  switch (status) {
    case "active":
      color = "#22c55e";
      break;
    case "degraded":
      color = "#eab308";
      break;
    case "offline":
    case "error":
      color = "#ef4444";
      break;
    case "maintenance":
      color = "#6b7280";
      break;
    default:
      color = "#6b7280";
  }

  return L.divIcon({
    className: "custom-camera-marker",
    html: `<div style="
      width: 14px;
      height: 14px;
      background-color: ${color};
      border: 2px solid rgba(255,255,255,0.8);
      border-radius: 50%;
      box-shadow: 0 0 6px ${color}80;
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -10],
  });
}

export default function CameraMarker({ camera }: CameraMarkerProps) {
  return (
    <Marker
      position={[camera.latitude, camera.longitude]}
      icon={getMarkerIcon(camera.status)}
    >
      <Popup>
        <div className="min-w-[180px]">
          <p className="font-semibold text-sm mb-1">{camera.name}</p>
          <div className="space-y-0.5 text-xs">
            <p>
              <span className="text-gray-400">Status: </span>
              <span
                className={
                  camera.status === "active"
                    ? "text-green-400"
                    : camera.status === "degraded"
                    ? "text-yellow-400"
                    : "text-red-400"
                }
              >
                {camera.status}
              </span>
            </p>
            <p>
              <span className="text-gray-400">Interstate: </span>
              {camera.interstate}
              {camera.direction ? ` ${camera.direction}` : ""}
            </p>
            {camera.fps_actual !== null && (
              <p>
                <span className="text-gray-400">FPS: </span>
                {camera.fps_actual.toFixed(1)}
              </p>
            )}
            <p>
              <span className="text-gray-400">Last frame: </span>
              {camera.last_frame_at
                ? formatRelativeTime(camera.last_frame_at)
                : "N/A"}
            </p>
          </div>
        </div>
      </Popup>
    </Marker>
  );
}

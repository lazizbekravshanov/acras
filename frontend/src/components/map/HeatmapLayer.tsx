"use client";

import { CircleMarker, Tooltip } from "react-leaflet";
import type { HeatmapPoint } from "@/lib/types";

interface HeatmapLayerProps {
  points: HeatmapPoint[];
}

function intensityToColor(intensity: number): string {
  // Gradient from blue (low) -> yellow (mid) -> red (high)
  if (intensity < 0.33) {
    return `rgba(59, 130, 246, ${0.3 + intensity * 1.5})`;
  } else if (intensity < 0.66) {
    return `rgba(245, 158, 11, ${0.4 + intensity * 0.6})`;
  } else {
    return `rgba(239, 68, 68, ${0.5 + intensity * 0.5})`;
  }
}

function intensityToRadius(intensity: number): number {
  return 8 + intensity * 20;
}

export default function HeatmapLayer({ points }: HeatmapLayerProps) {
  return (
    <>
      {points.map((point, index) => (
        <CircleMarker
          key={`heatmap-${index}`}
          center={[point.latitude, point.longitude]}
          radius={intensityToRadius(point.intensity)}
          pathOptions={{
            color: "transparent",
            fillColor: intensityToColor(point.intensity),
            fillOpacity: 0.6 + point.intensity * 0.3,
          }}
        >
          <Tooltip>
            <div className="text-xs">
              <p className="font-semibold">
                {point.incident_count} incident
                {point.incident_count !== 1 ? "s" : ""}
              </p>
              <p className="text-gray-400">
                Intensity: {(point.intensity * 100).toFixed(0)}%
              </p>
            </div>
          </Tooltip>
        </CircleMarker>
      ))}
    </>
  );
}

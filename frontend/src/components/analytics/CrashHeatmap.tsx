"use client";

import dynamic from "next/dynamic";
import type { HeatmapPoint } from "@/lib/types";

const LiveMap = dynamic(() => import("@/components/map/LiveMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center rounded-lg bg-surface-card">
      <div className="text-sm text-gray-500">Loading map...</div>
    </div>
  ),
});

interface CrashHeatmapProps {
  points: HeatmapPoint[];
  className?: string;
}

export default function CrashHeatmap({
  points,
  className = "",
}: CrashHeatmapProps) {
  return (
    <div className={`h-full w-full ${className}`}>
      <LiveMap
        heatmapPoints={points}
        showHeatmap={true}
        cameras={[]}
        incidents={[]}
      />
    </div>
  );
}

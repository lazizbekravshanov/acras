"use client";

import Link from "next/link";
import { Video, Wifi } from "lucide-react";
import type { Camera } from "@/lib/types";
import CameraStatus from "./CameraStatus";
import { cn } from "@/lib/utils";

interface CameraFeedProps {
  camera: Camera;
}

export default function CameraFeed({ camera }: CameraFeedProps) {
  return (
    <Link href={`/cameras/${camera.id}`}>
      <div className="rounded-lg border border-surface-border bg-surface-card overflow-hidden hover:border-surface-elevated transition-colors cursor-pointer group">
        {/* Thumbnail / Placeholder */}
        <div className="relative aspect-video bg-surface-elevated flex items-center justify-center overflow-hidden">
          <div className="flex flex-col items-center gap-2 text-gray-600">
            <Video className="h-10 w-10" />
            <span className="text-xs">
              {camera.stream_type.toUpperCase()} Feed
            </span>
          </div>

          {/* FPS badge */}
          {camera.fps_actual !== null && camera.fps_actual > 0 && (
            <div className="absolute top-2 right-2 flex items-center gap-1 rounded bg-black/60 px-1.5 py-0.5 text-[10px] font-mono text-green-400">
              <Wifi className="h-3 w-3" />
              {camera.fps_actual.toFixed(0)} FPS
            </div>
          )}

          {/* Status overlay */}
          <div className="absolute top-2 left-2">
            <CameraStatus status={camera.status} />
          </div>

          {/* Hover overlay */}
          <div className="absolute inset-0 bg-accent/5 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>

        {/* Info */}
        <div className="p-3">
          <h3 className="text-sm font-semibold text-gray-100 truncate">
            {camera.name}
          </h3>
          <p className="text-xs text-gray-500 mt-0.5 truncate">
            {camera.interstate}
            {camera.direction ? ` ${camera.direction}` : ""} &middot;{" "}
            {camera.state_code}
            {camera.mile_marker !== null
              ? ` &middot; MM ${camera.mile_marker}`
              : ""}
          </p>
        </div>
      </div>
    </Link>
  );
}

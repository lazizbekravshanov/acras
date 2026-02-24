"use client";

import { useState, useEffect, useCallback } from "react";
import { Filter, Camera as CameraIcon } from "lucide-react";
import { api } from "@/lib/api";
import type { Camera } from "@/lib/types";
import CameraFeed from "@/components/cameras/CameraFeed";

const STATUS_OPTIONS = ["", "active", "inactive", "degraded", "error", "maintenance"];
const PAGE_SIZE = 100;

export default function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [interstateFilter, setInterstateFilter] = useState("");

  const fetchCameras = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getCameras({
        page: 1,
        page_size: PAGE_SIZE,
        status: statusFilter || undefined,
        state_code: stateFilter || undefined,
        interstate: interstateFilter || undefined,
      });
      setCameras(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch cameras"
      );
    } finally {
      setLoading(false);
    }
  }, [statusFilter, stateFilter, interstateFilter]);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  // Compute unique states and interstates for filter dropdowns
  const uniqueStates = Array.from(new Set(cameras.map((c) => c.state_code))).sort();
  const uniqueInterstates = Array.from(
    new Set(cameras.map((c) => c.interstate))
  ).sort();

  const activeCount = cameras.filter((c) => c.status === "active").length;
  const inactiveCount = cameras.length - activeCount;

  return (
    <div className="space-y-6">
      {/* Stats Bar */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <CameraIcon className="h-5 w-5 text-gray-500" />
          <span className="text-sm text-gray-400">
            <span className="font-semibold text-gray-100">{total}</span> total
            cameras
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-green-500" />
          <span className="text-sm text-gray-400">
            <span className="font-semibold text-green-400">{activeCount}</span>{" "}
            active
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-red-500" />
          <span className="text-sm text-gray-400">
            <span className="font-semibold text-red-400">{inactiveCount}</span>{" "}
            inactive
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-500">Filters:</span>
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-9 rounded-lg border border-surface-border bg-surface-card px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        >
          <option value="">All Statuses</option>
          {STATUS_OPTIONS.filter(Boolean).map((s) => (
            <option key={s} value={s}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>

        <select
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          className="h-9 rounded-lg border border-surface-border bg-surface-card px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        >
          <option value="">All States</option>
          {uniqueStates.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <select
          value={interstateFilter}
          onChange={(e) => setInterstateFilter(e.target.value)}
          className="h-9 rounded-lg border border-surface-border bg-surface-card px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        >
          <option value="">All Interstates</option>
          {uniqueInterstates.map((i) => (
            <option key={i} value={i}>
              {i}
            </option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Camera Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className="aspect-video animate-pulse rounded-lg bg-surface-card"
            />
          ))}
        </div>
      ) : cameras.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-500">
          <CameraIcon className="h-12 w-12 mb-3 opacity-50" />
          <p className="text-sm font-medium">No cameras found</p>
          <p className="text-xs mt-1">Adjust your filters or add cameras.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {cameras.map((camera) => (
            <CameraFeed key={camera.id} camera={camera} />
          ))}
        </div>
      )}
    </div>
  );
}

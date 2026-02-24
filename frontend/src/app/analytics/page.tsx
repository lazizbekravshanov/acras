"use client";

import { useEffect, useState } from "react";
import { Calendar, TrendingUp, MapPin, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import type { TrendDataPoint, HeatmapPoint } from "@/lib/types";
import TimeSeriesChart from "@/components/analytics/TimeSeriesChart";
import SeverityDistribution from "@/components/analytics/SeverityDistribution";
import CrashHeatmap from "@/components/analytics/CrashHeatmap";

type PeriodType = "hourly" | "daily" | "weekly";

export default function AnalyticsPage() {
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([]);
  const [heatmapPoints, setHeatmapPoints] = useState<HeatmapPoint[]>([]);
  const [totalIncidents, setTotalIncidents] = useState(0);
  const [loading, setLoading] = useState(true);

  // Controls
  const [period, setPeriod] = useState<PeriodType>("daily");
  const [days, setDays] = useState(30);

  useEffect(() => {
    async function fetchAnalytics() {
      setLoading(true);
      try {
        const [trendResponse, heatmapResponse] = await Promise.all([
          api.getTrends({ period, days }),
          api.getHeatmap(),
        ]);
        setTrendData(trendResponse.data);
        setTotalIncidents(trendResponse.total);
        setHeatmapPoints(heatmapResponse.points);
      } catch {
        // API may not be available
        setTrendData([]);
        setHeatmapPoints([]);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, [period, days]);

  // Compute top dangerous locations from heatmap data
  const topLocations = [...heatmapPoints]
    .sort((a, b) => b.incident_count - a.incident_count)
    .slice(0, 10);

  return (
    <div className="space-y-6">
      {/* Date Range Selector */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Calendar className="h-5 w-5 text-gray-500" />
          <span className="text-sm text-gray-400">Time Range:</span>

          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="h-9 rounded-lg border border-surface-border bg-surface-card px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>

          <span className="text-sm text-gray-400">Granularity:</span>

          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as PeriodType)}
            className="h-9 rounded-lg border border-surface-border bg-surface-card px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-surface-border bg-surface-card px-3 py-2">
          <TrendingUp className="h-4 w-4 text-accent" />
          <span className="text-sm text-gray-100 font-semibold">
            {totalIncidents}
          </span>
          <span className="text-xs text-gray-500">total incidents</span>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time Series (2/3) */}
        <div className="lg:col-span-2 rounded-lg border border-surface-border bg-surface-card p-5">
          <h3 className="text-sm font-semibold text-gray-100 mb-4">
            Incident Trends
          </h3>
          {loading ? (
            <div className="h-[300px] animate-pulse rounded bg-surface-elevated" />
          ) : (
            <TimeSeriesChart data={trendData} height={300} />
          )}
        </div>

        {/* Severity Pie (1/3) */}
        <div className="rounded-lg border border-surface-border bg-surface-card p-5">
          <h3 className="text-sm font-semibold text-gray-100 mb-4">
            Severity Distribution
          </h3>
          {loading ? (
            <div className="h-[300px] animate-pulse rounded bg-surface-elevated" />
          ) : (
            <SeverityDistribution data={trendData} height={300} />
          )}
        </div>
      </div>

      {/* Heatmap + Top Locations Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Heatmap (2/3) */}
        <div className="lg:col-span-2 rounded-lg border border-surface-border bg-surface-card p-5">
          <h3 className="text-sm font-semibold text-gray-100 mb-4">
            Crash Heatmap
          </h3>
          {loading ? (
            <div className="h-[400px] animate-pulse rounded bg-surface-elevated" />
          ) : (
            <div style={{ height: "400px" }}>
              <CrashHeatmap points={heatmapPoints} />
            </div>
          )}
        </div>

        {/* Top Dangerous Locations (1/3) */}
        <div className="rounded-lg border border-surface-border bg-surface-card p-5">
          <h3 className="text-sm font-semibold text-gray-100 mb-4 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            Top Dangerous Locations
          </h3>
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="h-12 animate-pulse rounded bg-surface-elevated"
                />
              ))}
            </div>
          ) : topLocations.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">
              No location data available
            </p>
          ) : (
            <div className="space-y-2">
              {topLocations.map((loc, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg bg-surface-elevated p-3"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-surface-card text-xs font-bold text-gray-400">
                      {index + 1}
                    </span>
                    <div>
                      <p className="text-xs text-gray-100 font-mono">
                        {loc.latitude.toFixed(3)}, {loc.longitude.toFixed(3)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-red-400" />
                    <span className="text-sm font-semibold text-red-400">
                      {loc.incident_count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

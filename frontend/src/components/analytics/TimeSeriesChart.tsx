"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";
import type { TrendDataPoint } from "@/lib/types";

interface TimeSeriesChartProps {
  data: TrendDataPoint[];
  height?: number;
}

function formatXTick(timestamp: string): string {
  try {
    return format(new Date(timestamp), "MMM d");
  } catch {
    return timestamp;
  }
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    payload: TrendDataPoint;
  }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const point = payload[0].payload;
  let dateStr: string;
  try {
    dateStr = format(new Date(label || ""), "MMM d, yyyy HH:mm");
  } catch {
    dateStr = label || "";
  }

  return (
    <div className="rounded-lg border border-surface-border bg-surface-card p-3 shadow-lg">
      <p className="text-xs text-gray-400 mb-1">{dateStr}</p>
      <p className="text-sm font-semibold text-gray-100">
        {point.count} incident{point.count !== 1 ? "s" : ""}
      </p>
      {point.severity_breakdown &&
        Object.keys(point.severity_breakdown).length > 0 && (
          <div className="mt-1 space-y-0.5">
            {Object.entries(point.severity_breakdown).map(
              ([sev, count]) => (
                <p key={sev} className="text-xs text-gray-500 capitalize">
                  {sev}: {count}
                </p>
              )
            )}
          </div>
        )}
    </div>
  );
}

export default function TimeSeriesChart({
  data,
  height = 300,
}: TimeSeriesChartProps) {
  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-gray-500 text-sm"
        style={{ height }}
      >
        No trend data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart
        data={data}
        margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
      >
        <defs>
          <linearGradient id="incidentGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#2a2a3a"
          vertical={false}
        />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatXTick}
          stroke="#4a4a5a"
          tick={{ fill: "#9ca3af", fontSize: 12 }}
          axisLine={{ stroke: "#2a2a3a" }}
        />
        <YAxis
          stroke="#4a4a5a"
          tick={{ fill: "#9ca3af", fontSize: 12 }}
          axisLine={{ stroke: "#2a2a3a" }}
          allowDecimals={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#6366f1"
          strokeWidth={2}
          fill="url(#incidentGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

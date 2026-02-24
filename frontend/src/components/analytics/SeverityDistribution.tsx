"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import type { TrendDataPoint } from "@/lib/types";

interface SeverityDistributionProps {
  data: TrendDataPoint[];
  height?: number;
}

const SEVERITY_COLORS: Record<string, string> = {
  minor: "#3b82f6",
  moderate: "#f59e0b",
  severe: "#f97316",
  critical: "#ef4444",
};

interface PieDataEntry {
  name: string;
  value: number;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: PieDataEntry;
    value: number;
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const entry = payload[0].payload;
  return (
    <div className="rounded-lg border border-surface-border bg-surface-card p-3 shadow-lg">
      <p className="text-sm font-semibold capitalize" style={{ color: entry.color }}>
        {entry.name}
      </p>
      <p className="text-xs text-gray-400 mt-0.5">
        {entry.value} incident{entry.value !== 1 ? "s" : ""}
      </p>
    </div>
  );
}

interface CustomLabelProps {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  percent: number;
}

function renderCustomLabel({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
}: CustomLabelProps) {
  if (percent < 0.05) return null;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={12}
      fontWeight={600}
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

export default function SeverityDistribution({
  data,
  height = 300,
}: SeverityDistributionProps) {
  // Aggregate severity breakdown across all data points
  const severityCounts: Record<string, number> = {};
  data.forEach((point) => {
    if (point.severity_breakdown) {
      Object.entries(point.severity_breakdown).forEach(([sev, count]) => {
        severityCounts[sev] = (severityCounts[sev] || 0) + count;
      });
    }
  });

  const pieData: PieDataEntry[] = Object.entries(severityCounts)
    .filter(([, count]) => count > 0)
    .map(([name, value]) => ({
      name,
      value,
      color: SEVERITY_COLORS[name] || "#6b7280",
    }));

  if (pieData.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-gray-500 text-sm"
        style={{ height }}
      >
        No severity data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={pieData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={3}
          dataKey="value"
          label={renderCustomLabel}
          labelLine={false}
        >
          {pieData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          formatter={(value: string) => (
            <span className="text-xs text-gray-400 capitalize">{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

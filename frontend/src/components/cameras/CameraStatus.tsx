"use client";

import { cn, statusColor } from "@/lib/utils";

interface CameraStatusProps {
  status: string;
  className?: string;
}

const statusLabels: Record<string, string> = {
  active: "Active",
  degraded: "Degraded",
  offline: "Offline",
  error: "Offline",
  maintenance: "Maintenance",
  inactive: "Inactive",
};

export default function CameraStatus({
  status,
  className,
}: CameraStatusProps) {
  const colors = statusColor(status);
  const label = statusLabels[status] || status;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs font-medium",
        colors.text,
        className
      )}
    >
      <span className={cn("h-2 w-2 rounded-full", colors.dot)} />
      {label}
    </span>
  );
}

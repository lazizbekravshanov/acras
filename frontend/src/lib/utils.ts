import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow, format } from "date-fns";

/**
 * Merge Tailwind CSS classes with clsx and tailwind-merge.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a date string or Date to a human-readable date/time.
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return "N/A";
  const d = typeof date === "string" ? new Date(date) : date;
  return format(d, "MMM d, yyyy HH:mm");
}

/**
 * Format a date string or Date to relative time (e.g. "5 minutes ago").
 */
export function formatRelativeTime(
  date: string | Date | null | undefined
): string {
  if (!date) return "N/A";
  const d = typeof date === "string" ? new Date(date) : date;
  return formatDistanceToNow(d, { addSuffix: true });
}

/**
 * Return Tailwind color classes for a severity level.
 */
export function severityColor(severity: string): {
  bg: string;
  text: string;
  border: string;
  dot: string;
} {
  switch (severity) {
    case "minor":
      return {
        bg: "bg-blue-500/20",
        text: "text-blue-400",
        border: "border-blue-500",
        dot: "bg-blue-500",
      };
    case "moderate":
      return {
        bg: "bg-amber-500/20",
        text: "text-amber-400",
        border: "border-amber-500",
        dot: "bg-amber-500",
      };
    case "severe":
      return {
        bg: "bg-orange-500/20",
        text: "text-orange-400",
        border: "border-orange-500",
        dot: "bg-orange-500",
      };
    case "critical":
      return {
        bg: "bg-red-500/20",
        text: "text-red-400",
        border: "border-red-500",
        dot: "bg-red-500",
      };
    default:
      return {
        bg: "bg-gray-500/20",
        text: "text-gray-400",
        border: "border-gray-500",
        dot: "bg-gray-500",
      };
  }
}

/**
 * Return Tailwind color classes for a status value.
 */
export function statusColor(status: string): {
  bg: string;
  text: string;
  dot: string;
} {
  switch (status) {
    case "active":
      return {
        bg: "bg-green-500/20",
        text: "text-green-400",
        dot: "bg-green-500",
      };
    case "detected":
      return {
        bg: "bg-yellow-500/20",
        text: "text-yellow-400",
        dot: "bg-yellow-500",
      };
    case "confirmed":
      return {
        bg: "bg-orange-500/20",
        text: "text-orange-400",
        dot: "bg-orange-500",
      };
    case "responding":
      return {
        bg: "bg-blue-500/20",
        text: "text-blue-400",
        dot: "bg-blue-500",
      };
    case "clearing":
      return {
        bg: "bg-indigo-500/20",
        text: "text-indigo-400",
        dot: "bg-indigo-500",
      };
    case "resolved":
      return {
        bg: "bg-green-500/20",
        text: "text-green-400",
        dot: "bg-green-500",
      };
    case "false_positive":
      return {
        bg: "bg-gray-500/20",
        text: "text-gray-400",
        dot: "bg-gray-500",
      };
    case "degraded":
      return {
        bg: "bg-yellow-500/20",
        text: "text-yellow-400",
        dot: "bg-yellow-500",
      };
    case "offline":
    case "error":
      return {
        bg: "bg-red-500/20",
        text: "text-red-400",
        dot: "bg-red-500",
      };
    case "maintenance":
      return {
        bg: "bg-gray-500/20",
        text: "text-gray-400",
        dot: "bg-gray-500",
      };
    default:
      return {
        bg: "bg-gray-500/20",
        text: "text-gray-400",
        dot: "bg-gray-500",
      };
  }
}

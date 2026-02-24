/**
 * TypeScript interfaces matching the backend Pydantic schemas exactly.
 */

// ── Camera ──────────────────────────────────────────────────────────────────

export interface Camera {
  id: string;
  name: string;
  description: string | null;
  stream_url: string;
  stream_type: "rtsp" | "mjpeg" | "hls" | "http_image";
  latitude: number;
  longitude: number;
  state_code: string;
  interstate: string;
  direction: string | null;
  mile_marker: number | null;
  source_agency: string | null;
  metadata: Record<string, unknown>;
  status: string;
  last_frame_at: string | null;
  fps_actual: number | null;
  resolution_width: number | null;
  resolution_height: number | null;
  created_at: string;
  updated_at: string;
}

export interface CameraListResponse {
  items: Camera[];
  total: number;
  page: number;
  page_size: number;
}

// ── Incident ────────────────────────────────────────────────────────────────

export type IncidentType =
  | "crash"
  | "stall"
  | "debris"
  | "fire"
  | "wrong_way"
  | "pedestrian"
  | "weather_hazard"
  | "unknown";

export type Severity = "minor" | "moderate" | "severe" | "critical";

export type IncidentStatus =
  | "detected"
  | "confirmed"
  | "responding"
  | "clearing"
  | "resolved"
  | "false_positive";

export interface Incident {
  id: string;
  camera_id: string;
  incident_type: IncidentType;
  severity: Severity;
  severity_score: number;
  confidence: number;
  status: IncidentStatus;
  latitude: number;
  longitude: number;
  interstate: string;
  direction: string | null;
  lane_impact: string | null;
  vehicle_count: number | null;
  detected_at: string;
  confirmed_at: string | null;
  resolved_at: string | null;
  thumbnail_url: string | null;
  weather_conditions: Record<string, unknown> | null;
  detection_frames: unknown[];
  created_at: string;
  updated_at: string;
}

export interface IncidentListResponse {
  items: Incident[];
  total: number;
  page: number;
  page_size: number;
}

export interface IncidentUpdate {
  status?: IncidentStatus;
  severity?: Severity;
  severity_score?: number;
  confidence?: number;
  lane_impact?: string;
  vehicle_count?: number;
}

// ── Report ──────────────────────────────────────────────────────────────────

export interface Report {
  id: string;
  incident_id: string;
  report_type: string;
  structured_data: Record<string, unknown>;
  narrative: string;
  pdf_url: string | null;
  version: number;
  generated_by: string;
  created_at: string;
}

export interface ReportListResponse {
  items: Report[];
  total: number;
  page: number;
  page_size: number;
}

// ── Alert ───────────────────────────────────────────────────────────────────

export type AlertChannel = "webhook" | "email" | "sms" | "websocket" | "push";

export interface AlertConfig {
  id: string;
  name: string;
  channel: AlertChannel;
  recipient: string;
  min_severity: Severity;
  incident_types: string[];
  interstates: string[] | null;
  is_active: boolean;
  cooldown_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface AlertConfigCreate {
  name: string;
  channel: AlertChannel;
  recipient: string;
  min_severity?: Severity;
  incident_types?: string[];
  interstates?: string[] | null;
  is_active?: boolean;
  cooldown_minutes?: number;
}

export interface Alert {
  id: string;
  incident_id: string;
  channel: string;
  recipient: string;
  status: string;
  payload: Record<string, unknown>;
  sent_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface AlertListResponse {
  items: Alert[];
  total: number;
  page: number;
  page_size: number;
}

// ── Analytics ───────────────────────────────────────────────────────────────

export interface HeatmapPoint {
  latitude: number;
  longitude: number;
  intensity: number;
  incident_count: number;
}

export interface HeatmapResponse {
  points: HeatmapPoint[];
  total_incidents: number;
  period_start: string;
  period_end: string;
}

export interface TrendDataPoint {
  timestamp: string;
  count: number;
  severity_breakdown: Record<string, number>;
}

export interface TrendResponse {
  period: string;
  data: TrendDataPoint[];
  total: number;
}

export interface RiskScoreResponse {
  latitude: number;
  longitude: number;
  risk_score: number;
  risk_level: string;
  factors: string[];
  historical_incidents_30d: number;
  prediction_confidence: number;
}

export interface SummaryStats {
  active_cameras: number;
  active_incidents: number;
  incidents_today: number;
  incidents_this_week: number;
  avg_detection_time_seconds: number | null;
  avg_resolution_time_minutes: number | null;
  false_positive_rate: number | null;
  top_severity: string | null;
}

// ── WebSocket Messages ──────────────────────────────────────────────────────

export interface WebSocketMessage {
  type: string;
  data?: unknown;
}

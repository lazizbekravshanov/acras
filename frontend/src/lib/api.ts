import type {
  Camera,
  CameraListResponse,
  Incident,
  IncidentListResponse,
  IncidentUpdate,
  Report,
  ReportListResponse,
  AlertConfig,
  AlertConfigCreate,
  HeatmapResponse,
  TrendResponse,
  RiskScoreResponse,
  SummaryStats,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Lightweight API client wrapping fetch with typed methods
 * matching the backend FastAPI endpoints.
 */
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!res.ok) {
      const errorBody = await res.text().catch(() => "Unknown error");
      throw new Error(
        `API error ${res.status}: ${res.statusText} - ${errorBody}`
      );
    }

    if (res.status === 204) {
      return undefined as T;
    }

    return res.json();
  }

  // ── Cameras ─────────────────────────────────────────────────────────────

  async getCameras(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    state_code?: string;
    interstate?: string;
  }): Promise<CameraListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    if (params?.status) query.set("status", params.status);
    if (params?.state_code) query.set("state_code", params.state_code);
    if (params?.interstate) query.set("interstate", params.interstate);
    const qs = query.toString();
    return this.request<CameraListResponse>(
      `/cameras${qs ? `?${qs}` : ""}`
    );
  }

  async getCamera(id: string): Promise<Camera> {
    return this.request<Camera>(`/cameras/${id}`);
  }

  // ── Incidents ───────────────────────────────────────────────────────────

  async getIncidents(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    severity?: string;
    incident_type?: string;
    camera_id?: string;
    interstate?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<IncidentListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    if (params?.status) query.set("status", params.status);
    if (params?.severity) query.set("severity", params.severity);
    if (params?.incident_type)
      query.set("incident_type", params.incident_type);
    if (params?.camera_id) query.set("camera_id", params.camera_id);
    if (params?.interstate) query.set("interstate", params.interstate);
    if (params?.start_date) query.set("start_date", params.start_date);
    if (params?.end_date) query.set("end_date", params.end_date);
    const qs = query.toString();
    return this.request<IncidentListResponse>(
      `/incidents${qs ? `?${qs}` : ""}`
    );
  }

  async getIncident(id: string): Promise<Incident> {
    return this.request<Incident>(`/incidents/${id}`);
  }

  async updateIncident(
    id: string,
    data: IncidentUpdate
  ): Promise<Incident> {
    return this.request<Incident>(`/incidents/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // ── Reports ─────────────────────────────────────────────────────────────

  async getReports(params?: {
    page?: number;
    page_size?: number;
    incident_id?: string;
  }): Promise<ReportListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    if (params?.incident_id) query.set("incident_id", params.incident_id);
    const qs = query.toString();
    return this.request<ReportListResponse>(
      `/reports${qs ? `?${qs}` : ""}`
    );
  }

  async getReport(id: string): Promise<Report> {
    return this.request<Report>(`/reports/${id}`);
  }

  // ── Analytics ───────────────────────────────────────────────────────────

  async getSummary(): Promise<SummaryStats> {
    return this.request<SummaryStats>("/analytics/summary");
  }

  async getHeatmap(params?: {
    start_date?: string;
    end_date?: string;
    severity?: string;
  }): Promise<HeatmapResponse> {
    const query = new URLSearchParams();
    if (params?.start_date) query.set("start_date", params.start_date);
    if (params?.end_date) query.set("end_date", params.end_date);
    if (params?.severity) query.set("severity", params.severity);
    const qs = query.toString();
    return this.request<HeatmapResponse>(
      `/analytics/heatmap${qs ? `?${qs}` : ""}`
    );
  }

  async getTrends(params?: {
    period?: string;
    days?: number;
  }): Promise<TrendResponse> {
    const query = new URLSearchParams();
    if (params?.period) query.set("period", params.period);
    if (params?.days) query.set("days", String(params.days));
    const qs = query.toString();
    return this.request<TrendResponse>(
      `/analytics/trends${qs ? `?${qs}` : ""}`
    );
  }

  async getRisk(lat: number, lon: number): Promise<RiskScoreResponse> {
    return this.request<RiskScoreResponse>(
      `/analytics/risk?lat=${lat}&lon=${lon}`
    );
  }

  // ── Alerts ──────────────────────────────────────────────────────────────

  async getAlertConfigs(): Promise<AlertConfig[]> {
    return this.request<AlertConfig[]>("/alerts/configs");
  }

  async createAlertConfig(
    data: AlertConfigCreate
  ): Promise<AlertConfig> {
    return this.request<AlertConfig>("/alerts/configs", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateAlertConfig(
    id: string,
    data: Partial<AlertConfigCreate>
  ): Promise<AlertConfig> {
    return this.request<AlertConfig>(`/alerts/configs/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteAlertConfig(id: string): Promise<void> {
    return this.request<void>(`/alerts/configs/${id}`, {
      method: "DELETE",
    });
  }
}

export const api = new ApiClient(BASE_URL);

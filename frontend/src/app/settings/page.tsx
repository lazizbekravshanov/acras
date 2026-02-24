"use client";

import { useEffect, useState } from "react";
import {
  Bell,
  Plus,
  Trash2,
  Save,
  Shield,
  Key,
  Sliders,
  Power,
} from "lucide-react";
import { api } from "@/lib/api";
import type { AlertConfig, AlertConfigCreate, AlertChannel, Severity } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

const CHANNELS: AlertChannel[] = ["webhook", "email", "sms", "websocket", "push"];
const SEVERITIES: Severity[] = ["minor", "moderate", "severe", "critical"];
const INCIDENT_TYPES = [
  "crash",
  "stall",
  "debris",
  "fire",
  "wrong_way",
  "pedestrian",
  "weather_hazard",
];

export default function SettingsPage() {
  // Alert Configs
  const [configs, setConfigs] = useState<AlertConfig[]>([]);
  const [configsLoading, setConfigsLoading] = useState(true);
  const [configsError, setConfigsError] = useState<string | null>(null);

  // New Alert Config Form
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<AlertConfigCreate>({
    name: "",
    channel: "webhook",
    recipient: "",
    min_severity: "moderate",
    incident_types: ["crash"],
    cooldown_minutes: 5,
  });
  const [formSaving, setFormSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    fetchConfigs();
  }, []);

  async function fetchConfigs() {
    setConfigsLoading(true);
    setConfigsError(null);
    try {
      const data = await api.getAlertConfigs();
      setConfigs(data);
    } catch (err) {
      setConfigsError(
        err instanceof Error ? err.message : "Failed to fetch alert configs"
      );
    } finally {
      setConfigsLoading(false);
    }
  }

  async function handleCreateConfig(e: React.FormEvent) {
    e.preventDefault();
    setFormSaving(true);
    setFormError(null);
    try {
      const created = await api.createAlertConfig(formData);
      setConfigs((prev) => [created, ...prev]);
      setShowForm(false);
      setFormData({
        name: "",
        channel: "webhook",
        recipient: "",
        min_severity: "moderate",
        incident_types: ["crash"],
        cooldown_minutes: 5,
      });
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Failed to create alert config"
      );
    } finally {
      setFormSaving(false);
    }
  }

  async function handleDeleteConfig(id: string) {
    try {
      await api.deleteAlertConfig(id);
      setConfigs((prev) => prev.filter((c) => c.id !== id));
    } catch {
      // Failed to delete
    }
  }

  async function handleToggleActive(config: AlertConfig) {
    try {
      const updated = await api.updateAlertConfig(config.id, {
        is_active: !config.is_active,
      });
      setConfigs((prev) =>
        prev.map((c) => (c.id === updated.id ? updated : c))
      );
    } catch {
      // Failed to toggle
    }
  }

  function handleIncidentTypeToggle(type: string) {
    setFormData((prev) => {
      const types = prev.incident_types || [];
      if (types.includes(type)) {
        return {
          ...prev,
          incident_types: types.filter((t) => t !== type),
        };
      } else {
        return {
          ...prev,
          incident_types: [...types, type],
        };
      }
    });
  }

  return (
    <div className="max-w-4xl space-y-8">
      {/* Alert Configurations */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-semibold text-gray-100">
              Alert Configurations
            </h2>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-accent-hover transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Alert Rule
          </button>
        </div>

        {/* Create Form */}
        {showForm && (
          <form
            onSubmit={handleCreateConfig}
            className="rounded-lg border border-surface-border bg-surface-card p-5 mb-4 space-y-4"
          >
            <h3 className="text-sm font-semibold text-gray-100">
              Create Alert Rule
            </h3>

            {formError && (
              <div className="rounded border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-400">
                {formError}
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Name */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Rule Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="h-9 w-full rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-100 placeholder-gray-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  placeholder="e.g. Critical Crash Alerts"
                />
              </div>

              {/* Channel */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Channel
                </label>
                <select
                  value={formData.channel}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      channel: e.target.value as AlertChannel,
                    })
                  }
                  className="h-9 w-full rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  {CHANNELS.map((ch) => (
                    <option key={ch} value={ch}>
                      {ch.charAt(0).toUpperCase() + ch.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Recipient */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Recipient
                </label>
                <input
                  type="text"
                  required
                  value={formData.recipient}
                  onChange={(e) =>
                    setFormData({ ...formData, recipient: e.target.value })
                  }
                  className="h-9 w-full rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-100 placeholder-gray-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  placeholder="URL, email, or phone"
                />
              </div>

              {/* Min Severity */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Minimum Severity
                </label>
                <select
                  value={formData.min_severity}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      min_severity: e.target.value as Severity,
                    })
                  }
                  className="h-9 w-full rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  {SEVERITIES.map((s) => (
                    <option key={s} value={s}>
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Cooldown */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Cooldown (minutes)
                </label>
                <input
                  type="number"
                  min={1}
                  value={formData.cooldown_minutes}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      cooldown_minutes: parseInt(e.target.value) || 5,
                    })
                  }
                  className="h-9 w-full rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
            </div>

            {/* Incident Types */}
            <div>
              <label className="block text-xs text-gray-500 mb-2">
                Incident Types
              </label>
              <div className="flex flex-wrap gap-2">
                {INCIDENT_TYPES.map((type) => {
                  const isSelected = (formData.incident_types || []).includes(
                    type
                  );
                  return (
                    <button
                      key={type}
                      type="button"
                      onClick={() => handleIncidentTypeToggle(type)}
                      className={cn(
                        "rounded-full px-3 py-1 text-xs font-medium capitalize transition-colors",
                        isSelected
                          ? "bg-accent/20 text-accent border border-accent/40"
                          : "bg-surface-elevated text-gray-400 border border-surface-border hover:border-gray-500"
                      )}
                    >
                      {type.replace(/_/g, " ")}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Submit */}
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="rounded-lg border border-surface-border px-4 py-1.5 text-sm text-gray-400 hover:bg-surface-elevated transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={formSaving}
                className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-1.5 text-sm font-medium text-white hover:bg-accent-hover transition-colors disabled:opacity-50"
              >
                <Save className="h-4 w-4" />
                {formSaving ? "Saving..." : "Create Rule"}
              </button>
            </div>
          </form>
        )}

        {/* Existing Configs */}
        {configsError && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400 mb-4">
            {configsError}
          </div>
        )}

        <div className="rounded-lg border border-surface-border bg-surface-card overflow-hidden">
          {configsLoading ? (
            <div className="space-y-0">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="flex items-center gap-4 border-b border-surface-border p-4"
                >
                  <div className="h-4 w-48 animate-pulse rounded bg-surface-elevated" />
                  <div className="h-4 w-20 animate-pulse rounded bg-surface-elevated" />
                </div>
              ))}
            </div>
          ) : configs.length === 0 ? (
            <div className="py-12 text-center text-sm text-gray-500">
              No alert configurations yet. Create one above.
            </div>
          ) : (
            configs.map((config) => (
              <div
                key={config.id}
                className="flex items-center justify-between border-b border-surface-border p-4 last:border-0 hover:bg-surface-elevated/50 transition-colors"
              >
                <div className="flex items-center gap-4 min-w-0">
                  <button
                    onClick={() => handleToggleActive(config)}
                    className={cn(
                      "rounded-full p-1.5 transition-colors",
                      config.is_active
                        ? "bg-green-500/20 text-green-400"
                        : "bg-gray-500/20 text-gray-500"
                    )}
                    title={
                      config.is_active ? "Disable" : "Enable"
                    }
                  >
                    <Power className="h-3.5 w-3.5" />
                  </button>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-100 truncate">
                      {config.name}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {config.channel} to {config.recipient} &middot;
                      min severity: {config.min_severity} &middot;
                      cooldown: {config.cooldown_minutes}min
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs text-gray-500">
                    {formatDate(config.created_at)}
                  </span>
                  <button
                    onClick={() => handleDeleteConfig(config.id)}
                    className="rounded p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Detection Settings */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Sliders className="h-5 w-5 text-amber-400" />
          <h2 className="text-lg font-semibold text-gray-100">
            Detection Thresholds
          </h2>
        </div>
        <div className="rounded-lg border border-surface-border bg-surface-card p-5 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                Minimum Confidence (%)
              </label>
              <input
                type="range"
                min={10}
                max={99}
                defaultValue={70}
                className="w-full accent-accent"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>10%</span>
                <span>70% (default)</span>
                <span>99%</span>
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1">
                Severity Score Threshold
              </label>
              <input
                type="range"
                min={0}
                max={100}
                defaultValue={30}
                className="w-full accent-accent"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0.0</span>
                <span>0.3 (default)</span>
                <span>1.0</span>
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1">
                Auto-confirm after (seconds)
              </label>
              <input
                type="number"
                defaultValue={60}
                min={10}
                max={600}
                className="h-9 w-full rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1">
                Auto-resolve after (minutes)
              </label>
              <input
                type="number"
                defaultValue={120}
                min={5}
                max={1440}
                className="h-9 w-full rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-100 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-1.5 text-sm font-medium text-white hover:bg-accent-hover transition-colors">
              <Save className="h-4 w-4" />
              Save Thresholds
            </button>
          </div>
        </div>
      </section>

      {/* API Key Section */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Key className="h-5 w-5 text-green-400" />
          <h2 className="text-lg font-semibold text-gray-100">API Access</h2>
        </div>
        <div className="rounded-lg border border-surface-border bg-surface-card p-5 space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              API Base URL
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={
                  process.env.NEXT_PUBLIC_API_URL ||
                  "http://localhost:8000/api/v1"
                }
                className="h-9 flex-1 rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-300 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">
              WebSocket URL
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={
                  process.env.NEXT_PUBLIC_WS_URL ||
                  "ws://localhost:8000/api/v1/ws"
                }
                className="h-9 flex-1 rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-300 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">
              API Key
            </label>
            <div className="flex items-center gap-2">
              <input
                type="password"
                readOnly
                value="acras-api-key-placeholder-xxxx"
                className="h-9 flex-1 rounded-lg border border-surface-border bg-surface-elevated px-3 text-sm text-gray-300 font-mono"
              />
              <button className="flex items-center gap-1.5 rounded-lg border border-surface-border px-3 py-1.5 text-xs text-gray-400 hover:bg-surface-elevated transition-colors">
                <Shield className="h-3.5 w-3.5" />
                Reveal
              </button>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Used for authenticated API endpoints (POST, PATCH, DELETE).
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

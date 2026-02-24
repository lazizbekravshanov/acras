"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type { Incident } from "@/lib/types";
import { api } from "@/lib/api";

const REFRESH_INTERVAL = 15000; // 15 seconds

interface UseIncidentsOptions {
  status?: string;
  severity?: string;
  page?: number;
  pageSize?: number;
  autoRefresh?: boolean;
}

interface UseIncidentsReturn {
  incidents: Incident[];
  total: number;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useIncidents(
  options: UseIncidentsOptions = {}
): UseIncidentsReturn {
  const {
    status,
    severity,
    page = 1,
    pageSize = 50,
    autoRefresh = true,
  } = options;

  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      const response = await api.getIncidents({
        page,
        page_size: pageSize,
        status: status || undefined,
        severity: severity || undefined,
      });
      if (mountedRef.current) {
        setIncidents(response.items);
        setTotal(response.total);
        setError(null);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch incidents"
        );
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [page, pageSize, status, severity]);

  useEffect(() => {
    mountedRef.current = true;
    setLoading(true);
    fetchData();

    let intervalId: ReturnType<typeof setInterval> | undefined;
    if (autoRefresh) {
      intervalId = setInterval(fetchData, REFRESH_INTERVAL);
    }

    return () => {
      mountedRef.current = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [fetchData, autoRefresh]);

  return { incidents, total, loading, error, refresh: fetchData };
}

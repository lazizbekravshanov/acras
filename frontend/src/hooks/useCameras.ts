"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type { Camera } from "@/lib/types";
import { api } from "@/lib/api";

const REFRESH_INTERVAL = 30000; // 30 seconds

interface UseCamerasOptions {
  status?: string;
  state_code?: string;
  interstate?: string;
  page?: number;
  pageSize?: number;
  autoRefresh?: boolean;
}

interface UseCamerasReturn {
  cameras: Camera[];
  total: number;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useCameras(
  options: UseCamerasOptions = {}
): UseCamerasReturn {
  const {
    status,
    state_code,
    interstate,
    page = 1,
    pageSize = 200,
    autoRefresh = true,
  } = options;

  const [cameras, setCameras] = useState<Camera[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      const response = await api.getCameras({
        page,
        page_size: pageSize,
        status: status || undefined,
        state_code: state_code || undefined,
        interstate: interstate || undefined,
      });
      if (mountedRef.current) {
        setCameras(response.items);
        setTotal(response.total);
        setError(null);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch cameras"
        );
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [page, pageSize, status, state_code, interstate]);

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

  return { cameras, total, loading, error, refresh: fetchData };
}

"use client";
import { useCallback, useEffect, useState } from "react";
import { api, errorMessage } from "./api";
export function useResource<T>(path: string) {
  const [resolvedPath, setResolvedPath] = useState(path);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setData(await api<T>(path)); setResolvedPath(path); } catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  }, [path]);
  useEffect(() => {
    let alive = true;
    async function run() {
      try { const value = await api<T>(path); if (alive) { setData(value); setResolvedPath(path); setError(""); } }
      catch (e) { if (alive) { setError(errorMessage(e)); setResolvedPath(path); setData(null); } }
      finally { if (alive) setLoading(false); }
    }
    void run();
    return () => { alive = false; };
  }, [path]);
  return { data: resolvedPath === path ? data : null, setData, error: resolvedPath === path ? error : "", loading: loading || resolvedPath !== path, reload: load };
}

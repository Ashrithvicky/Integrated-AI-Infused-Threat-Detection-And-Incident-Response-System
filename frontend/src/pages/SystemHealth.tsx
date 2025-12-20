// src/pages/SystemHealth.tsx
/*import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchSystemHealth } from "../api/client";

const ComponentRow: React.FC<{ title: string; value: any }> = ({ title, value }) => (
  <div style={{ display: "flex", justifyContent: "space-between", padding: 8, borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
    <strong>{title}</strong>
    <span style={{ fontFamily: "monospace" }}>{typeof value === "object" ? JSON.stringify(value) : String(value)}</span>
  </div>
);

const SystemHealthPage: React.FC = () => {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["system-health"],
    queryFn: fetchSystemHealth,
    refetchInterval: 15000, // poll every 15s
  });

  if (isLoading) return <div className="card">Loading system health…</div>;
  if (isError) return <div className="card error">Failed to load system health</div>;

  const ok = data?.ok;

  return (
    <div className="page">
      <h2>System Health</h2>
      <p>Last checked: {data?.timestamp}</p>

      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>Overview</h3>
          <div style={{ color: ok ? "var(--success)" : "var(--danger)" }}>{ok ? "OK" : "ISSUES"}</div>
        </div>

        <div>
          <ComponentRow title="MySQL" value={data?.components?.mysql} />
          <ComponentRow title="Redis" value={data?.components?.redis} />
          <ComponentRow title="Kafka" value={data?.components?.kafka} />
          <ComponentRow title="Model" value={data?.components?.model} />
        </div>
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <h3>Summary</h3>
        <div style={{ padding: 8 }}>
          <div>Alerts total: {data?.components?.mysql?.counts?.alerts_total ?? "-"}</div>
          <div>Alerts by severity: {JSON.stringify(data?.summary?.alerts_by_severity ?? {})}</div>
          <div>Events last hour: {data?.summary?.events_ingested_last_hour ?? "-"}</div>
          <div>Avg detection score (last hour): {Number(data?.summary?.avg_detection_score_last_hour ?? 0).toFixed(3)}</div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthPage; */

// src/components/SystemHealth.tsx
import React, { useEffect, useState } from "react";

type HealthPayload = {
  timestamp?: string;
  generated_at?: string;
  ok?: boolean;
  components?: {
    mysql?: any;
    redis?: any;
    kafka?: any;
    model?: any;
  };
  summary?: {
    alerts_total?: number | null;
    alerts_by_severity?: Record<string, number>;
    events_last_hour?: number | null;
    avg_detection_score_last_hour?: number;
  };
  import_error?: string | null;
};

export default function SystemHealth() {
  const [data, setData] = useState<HealthPayload | null>(null);
  const [loading, setLoading] = useState(false);

  // Read env in a way that works under CRA or Vite or plain window fallback.
  const apiUrl =
    // CRA (process.env available in CRA builds)
    (typeof process !== "undefined" &&
      (process as any).env &&
      (process as any).env.REACT_APP_API_URL) ||
    // Vite (import.meta.env)
    (typeof import.meta !== "undefined" &&
      (import.meta as any).env &&
      (import.meta as any).env.VITE_API_URL) ||
    // global fallback (you can also set window.__API_URL in index.html)
    (typeof (window as any).__API_URL !== "undefined" && (window as any).__API_URL) ||
    "http://localhost:8000";

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/system-health?minutes=60`);
      if (!res.ok) {
        const txt = await res.text();
        console.error("system-health failed:", res.status, txt);
        setData(null);
      } else {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      console.error("fetch system-health error", e);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const id = setInterval(fetchHealth, 10_000); // poll every 10s
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const summary = data?.summary ?? {};

  // backend may return timestamp OR generated_at — prefer timestamp then generated_at
  const lastChecked = data?.timestamp ?? (data as any)?.generated_at ?? "—";

  return (
    <div className="system-health">
      <h2>System Health</h2>
      <div>Last checked: {lastChecked}</div>

      <section className="overview">
        <h3>Overview</h3>
        <div>MySQL: {JSON.stringify(data?.components?.mysql ?? {})}</div>
        <div>Redis: {JSON.stringify(data?.components?.redis ?? {})}</div>
        <div>Kafka: {JSON.stringify(data?.components?.kafka ?? {})}</div>
        <div>Model: {JSON.stringify(data?.components?.model ?? {})}</div>
      </section>

      <section className="summary">
        <h3>Summary</h3>
        <div>Alerts total: {summary.alerts_total ?? "-"}</div>
        <div>Alerts by severity: {JSON.stringify(summary.alerts_by_severity ?? {})}</div>
        <div>Events last hour: {summary.events_last_hour == null ? "-" : summary.events_last_hour}</div>
        <div>Avg detection score (last hour): {summary.avg_detection_score_last_hour == null ? "-" : summary.avg_detection_score_last_hour.toFixed(3)}</div>

      </section>

      {loading && <div className="loading">Refreshing…</div>}
    </div>
  );
}



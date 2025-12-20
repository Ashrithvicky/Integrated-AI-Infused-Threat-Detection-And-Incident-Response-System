// src/pages/LogsPage.tsx
import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAlerts } from "../api/client";
import type { Alert } from "../types";

const LogsPage: React.FC = () => {
  const { data: alerts = [], isLoading, isError } = useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 5000,
  });

  const [selectedId, setSelectedId] = useState<number | null>(null);

  if (isLoading) return <div className="card">Loading logs…</div>;
  if (isError) return <div className="card error">Error loading logs.</div>;

  const selectedAlert = alerts.find((a: Alert) => a.id === selectedId) || alerts[0];

  return (
    <div className="page logs-page">
      <h2>Logs</h2>
      <div className="logs-layout">
        <div className="card logs-list">
          <h3>Alert Events</h3>
          <ul>
            {alerts.map((a: Alert) => (
              <li
                key={a.id}
                className={selectedId === a.id ? "log-item selected" : "log-item"}
                onClick={() => setSelectedId(a.id)}
              >
                <div className="log-title">
                  <span>{a.event_type || "unknown"}</span>
                  <span className="log-entity">{a.entity_id || "unknown"}</span>
                </div>
                <div className="log-meta">
                  <span>{a.alert_ts ? new Date(a.alert_ts).toLocaleString() : "-"}</span>
                  <span>{a.source || "-"}</span>
                </div>
              </li>
            ))}
            {alerts.length === 0 && <li>No alerts/logs yet.</li>}
          </ul>
        </div>

        <div className="card logs-detail">
          <h3>Selected Event JSON</h3>
          {selectedAlert ? (
            <div className="json-columns">
              <div>
                <h4>Raw</h4>
                <pre>{JSON.stringify(selectedAlert.raw ?? {}, null, 2)}</pre>
              </div>
              <div>
                <h4>Normalized</h4>
                <pre>{JSON.stringify(selectedAlert.normalized ?? {}, null, 2)}</pre>
              </div>
            </div>
          ) : (
            <p>No alert selected.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default LogsPage;

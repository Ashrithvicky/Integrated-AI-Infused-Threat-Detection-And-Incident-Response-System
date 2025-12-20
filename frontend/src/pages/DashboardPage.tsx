// src/pages/DashboardPage.tsx
/* import React, { useState, useEffect } from 'react';
import ThreatMetrics from '../components/ThreatMetrics';
import SystemHealth from '../components/SystemHealth';
import './DashboardPage.css';

const DashboardPage: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('24h');

  // Mock data for demonstration
  const systemMetrics = {
    totalAlerts: 128,
    threatsBlocked: 47,
    avgResponseTime: '42ms',
    systemHealth: 98.7,
    activeUsers: 2847,
    dataProcessed: '2.4TB',
  };

  return (
    <div className="dashboard-page">
      {/* Dashboard Header */ /*}
      <div className="dashboard-header">
        <h1>Security Dashboard</h1>
        <div className="dashboard-controls">
          <select 
            className="time-select"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
          <button className="btn-refresh">🔄 Refresh</button>
        </div>
      </div>

      {/* Top Metrics - Threat Metrics only */ /*}
      <div className="threat-metrics-container">
        <ThreatMetrics />
      </div>

      {/* Main Content Grid */ /*}
      <div className="dashboard-content-grid">
        {/* Left Panel - System Health */ /*}
        <div className="health-panel">
          <SystemHealth metrics={systemMetrics} />
        </div>

        {/* Right Panel - Quick Actions & Alert Stats */ /*}
        <div className="right-panel">
          {/* Quick Actions Card - Compact */ /*}
          <div className="card quick-actions-card">
            <div className="card-header">
              <h3>Quick Actions</h3>
              <span className="actions-subtitle">Immediate Response</span>
            </div>
            <div className="card-body quick-actions">
              <div className="quick-actions-grid">
                <button className="action-btn investigate compact">
                  <span className="action-icon">🔍</span>
                  <span className="action-title">Investigate</span>
                </button>
                <button className="action-btn isolate compact">
                  <span className="action-icon">🛡️</span>
                  <span className="action-title">Isolate</span>
                </button>
                <button className="action-btn enrich compact">
                  <span className="action-icon">📊</span>
                  <span className="action-title">Enrich</span>
                </button>
                <button className="action-btn escalate compact">
                  <span className="action-icon">⚡</span>
                  <span className="action-title">Escalate</span>
                </button>
                <button className="action-btn quarantine compact">
                  <span className="action-icon">🚫</span>
                  <span className="action-title">Quarantine</span>
                </button>
                <button className="action-btn playbook compact">
                  <span className="action-icon">📋</span>
                  <span className="action-title">Playbook</span>
                </button>
              </div>
            </div>
            <div className="card-footer">
              <div className="auto-response-status">
                <span className="status-indicator"></span>
                <span>Auto-response: Active</span>
              </div>
            </div>
          </div>

          {/* Alert Stats - Compact */ /*}
          <div className="compact-alert-stats">
            <div className="compact-stat-card critical">
              <div className="compact-stat-content">
                <div className="compact-stat-value">12</div>
                <div className="compact-stat-label">Critical</div>
                <div className="compact-stat-trend up">+3</div>
              </div>
            </div>
            <div className="compact-stat-card high">
              <div className="compact-stat-content">
                <div className="compact-stat-value">38</div>
                <div className="compact-stat-label">High</div>
                <div className="compact-stat-trend up">+8</div>
              </div>
            </div>
            <div className="compact-stat-card medium">
              <div className="compact-stat-content">
                <div className="compact-stat-value">42</div>
                <div className="compact-stat-label">Medium</div>
                <div className="compact-stat-trend down">-2</div>
              </div>
            </div>
            <div className="compact-stat-card low">
              <div className="compact-stat-content">
                <div className="compact-stat-value">36</div>
                <div className="compact-stat-label">Low</div>
                <div className="compact-stat-trend up">+5</div>
              </div>
            </div>
            <div className="compact-stat-card false">
              <div className="compact-stat-content">
                <div className="compact-stat-value">2*</div>
                <div className="compact-stat-label">False</div>
                <div className="compact-stat-trend down">-60%</div>
              </div>
            </div>
            <div className="compact-stat-card response">
              <div className="compact-stat-content">
                <div className="compact-stat-value">42ms</div>
                <div className="compact-stat-label">Response</div>
                <div className="compact-stat-trend down">-8%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage; */
// src/pages/DashboardPage.tsx
import React, { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAlerts, getSeverity } from "../api/client";
import type { Alert } from "../types";

const DashboardPage: React.FC = () => {
  const { data: alerts = [], isLoading, isError } = useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 5000, // refresh periodically
  });

  const total = (alerts ?? []).length;

  const { counts, topEntities, topEvents } = useMemo(() => {
    const byEntity = new Map<string, number>();
    const byEventType = new Map<string, number>();
    const counts = { high: 0, medium: 0, low: 0 };

    (alerts ?? []).forEach((a: Alert) => {
      const ent = a.entity_id || "unknown";
      byEntity.set(ent, (byEntity.get(ent) || 0) + 1);

      const ev = a.event_type || a.eventName || "unknown";
      byEventType.set(ev, (byEventType.get(ev) || 0) + 1);

      const sev = getSeverity(a);
      if (sev === "high") counts.high++;
      else if (sev === "medium") counts.medium++;
      else counts.low++;
    });

    const topEntities = Array.from(byEntity.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    const topEvents = Array.from(byEventType.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    return { counts, topEntities, topEvents };
  }, [alerts]);

  if (isLoading) return <div className="card">Loading dashboard…</div>;
  if (isError) return <div className="card error">Error loading dashboard.</div>;

  return (
    <div className="page">
      <header style={{ marginBottom: 20 }}>
        <h1 style={{ margin: 0 }}>Cloud Threat Detection &amp; Response</h1>
        <p style={{ margin: "6px 0 0 0", color: "#9aa3b2" }}>Overview</p>
      </header>

      <section style={{ display: "flex", gap: 16, marginBottom: 18 }}>
        <div className="card overview-card" style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: "#9aa3b2" }}>Total Alerts</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{total}</div>
        </div>

        <div className="card overview-card" style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: "#9aa3b2" }}>High Severity</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{counts.high}</div>
        </div>

        <div className="card overview-card" style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: "#9aa3b2" }}>Medium Severity</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{counts.medium}</div>
        </div>

        <div className="card overview-card" style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: "#9aa3b2" }}>Low Severity</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{counts.low}</div>
        </div>
      </section>

      <section className="grid" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Alerts by Severity</h3>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            <li style={{ display: "flex", justifyContent: "space-between", padding: "8px 0" }}>
              <span>High</span>
              <span className="severity severity-high" style={{ fontWeight: 700 }}>{counts.high}</span>
            </li>
            <li style={{ display: "flex", justifyContent: "space-between", padding: "8px 0" }}>
              <span>Medium</span>
              <span className="severity severity-medium" style={{ fontWeight: 700 }}>{counts.medium}</span>
            </li>
            <li style={{ display: "flex", justifyContent: "space-between", padding: "8px 0" }}>
              <span>Low</span>
              <span className="severity severity-low" style={{ fontWeight: 700 }}>{counts.low}</span>
            </li>
          </ul>
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>Top Entities by Alerts</h3>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {topEntities.length === 0 && <li>No entities yet.</li>}
            {topEntities.map(([ent, count]) => (
              <li key={ent} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}>
                <span>{ent}</span>
                <span>{count}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>Top Event Types</h3>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {topEvents.length === 0 && <li>No events yet.</li>}
            {topEvents.map(([ev, count]) => (
              <li key={ev} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}>
                <span>{ev}</span>
                <span>{count}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
};

export default DashboardPage;


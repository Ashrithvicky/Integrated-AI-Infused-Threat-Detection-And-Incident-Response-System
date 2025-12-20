// src/components/AlertsTable.tsx
/* import React, { useEffect, useState } from "react";
import { fetchAlerts, fetchAlert, sendAlertFeedback } from "../api/client";
import CorrelationPanel from '../components/CorrelationPanel';
import NeighbourList from '../components/NeighbourList';
import type { Alert, AlertDetail } from "../api/types";
import SeverityBadge from "./SeverityBadge";
import './AlertsTable.css';

interface AlertsTableProps {
  onEntitySelected?: (entityId: string | undefined) => void;
}

// Dummy data for demonstration
const DUMMY_ALERTS: Alert[] = [
  {
    id: "alert-001",
    entity_id: "user-8472",
    entity_type: "user",
    event_type: "Unusual Login",
    source: "EDR",
    detection_score: 0.942,
    ti_score: 0.876,
    correlation_score: 0.912,
    label: "problem",
    alert_ts: new Date().toISOString(),
    normalized: { location: "External", time_of_day: "03:15" }
  },
  {
    id: "alert-002",
    entity_id: "endpoint-1298",
    entity_type: "endpoint",
    event_type: "Malware Detected",
    source: "EDR",
    detection_score: 0.987,
    ti_score: 0.934,
    correlation_score: 0.956,
    label: "problem",
    alert_ts: new Date(Date.now() - 3600000).toISOString(),
    normalized: { file_hash: "a1b2c3d4", process_name: "malware.exe" }
  },
  {
    id: "alert-003",
    entity_id: "user-5623",
    entity_type: "user",
    event_type: "Data Exfiltration",
    source: "UEBA",
    detection_score: 0.823,
    ti_score: 0.645,
    correlation_score: 0.734,
    label: "problem",
    alert_ts: new Date(Date.now() - 7200000).toISOString(),
    normalized: { data_size: "2.4GB", destination: "external_ip" }
  },
  {
    id: "alert-004",
    entity_id: "network-3345",
    entity_type: "network",
    event_type: "Port Scan",
    source: "NDR",
    detection_score: 0.712,
    ti_score: 0.589,
    correlation_score: 0.651,
    label: "problem",
    alert_ts: new Date(Date.now() - 10800000).toISOString(),
    normalized: { ports: "22,80,443", source_ip: "10.0.0.45" }
  },
  {
    id: "alert-005",
    entity_id: "user-1124",
    entity_type: "user",
    event_type: "Normal Login",
    source: "SIEM",
    detection_score: 0.123,
    ti_score: 0.045,
    correlation_score: 0.084,
    label: "normal",
    alert_ts: new Date(Date.now() - 14400000).toISOString(),
    normalized: { location: "Internal", time_of_day: "09:30" }
  },
  {
    id: "alert-006",
    entity_id: "endpoint-5567",
    entity_type: "endpoint",
    event_type: "Config Drift",
    source: "Policy",
    detection_score: 0.456,
    ti_score: 0.231,
    correlation_score: 0.342,
    label: "problem",
    alert_ts: new Date(Date.now() - 18000000).toISOString(),
    normalized: { policy_violation: "firewall_disabled", severity: "high" }
  },
  {
    id: "alert-007",
    entity_id: "user-8891",
    entity_type: "user",
    event_type: "Normal Activity",
    source: "UEBA",
    detection_score: 0.089,
    ti_score: 0.012,
    correlation_score: 0.051,
    label: "problem",
    alert_ts: new Date(Date.now() - 21600000).toISOString(),
    normalized: { activity: "routine_access", risk_score: "low" }
  },
  {
    id: "alert-008",
    entity_id: "network-7788",
    entity_type: "network",
    event_type: "DDoS Attack",
    source: "NDR",
    detection_score: 0.998,
    ti_score: 0.978,
    correlation_score: 0.988,
    label: "normal",
    alert_ts: new Date(Date.now() - 25200000).toISOString(),
    normalized: { traffic_rate: "10Gbps", duration: "15min" }
  }
];

const DUMMY_DETAILS: { [key: string]: AlertDetail } = {
  "alert-001": {
    id: "alert-001",
    entity_id: "user-8472",
    entity_type: "user",
    event_type: "Unusual Login",
    source: "EDR",
    detection_score: 0.942,
    ti_score: 0.876,
    correlation_score: 0.912,
    label: "problem",
    explain: {
      reason: "Login from unusual location (Russia) at abnormal time (03:15 AM)",
      confidence: "High",
      mitre_techniques: ["T1078"],
      risk_factors: ["Geographical anomaly", "Time anomaly", "Failed MFA"]
    },
    explain_shap: {
      features: {
        "login_location": 0.45,
        "login_time": 0.32,
        "failed_attempts": 0.18,
        "device_new": 0.12
      }
    },
    raw: {
      timestamp: "2024-01-15T03:15:42Z",
      user: "admin@corp.com",
      ip: "95.213.255.56",
      country: "Russia",
      user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      success: false,
      mfa_required: true,
      mfa_passed: false
    },
    normalized: { location: "External", time_of_day: "03:15" }
  },
  "alert-002": {
    id: "alert-002",
    entity_id: "endpoint-1298",
    entity_type: "endpoint",
    event_type: "Malware Detected",
    source: "EDR",
    detection_score: 0.987,
    ti_score: 0.934,
    correlation_score: 0.956,
    label: "problem",
    explain: {
      reason: "Malicious process execution with persistence mechanism",
      confidence: "Very High",
      mitre_techniques: ["T1059", "T1543"],
      threat_intel: "Matches known ransomware signature"
    },
    explain_shap: {
      features: {
        "process_signature": 0.67,
        "network_connections": 0.45,
        "file_modifications": 0.38,
        "registry_changes": 0.29
      }
    },
    raw: {
      endpoint: "WS-1298",
      process: "C:\\Windows\\Temp\\encryptor.exe",
      hash: "a1b2c3d4e5f6",
      severity: "critical",
      actions: ["quarantined", "alerted"],
      virustotal: "65/72 detection"
    },
    normalized: { file_hash: "a1b2c3d4", process_name: "malware.exe" }
  },
  "alert-003": {
    id: "alert-003",
    entity_id: "user-5623",
    entity_type: "user",
    event_type: "Data Exfiltration",
    source: "UEBA",
    detection_score: 0.823,
    ti_score: 0.645,
    correlation_score: 0.734,
    label: "problem",
    explain: {
      reason: "Large data transfer to external IP address",
      confidence: "Medium",
      mitre_techniques: ["T1048"],
      risk_factors: ["Large data volume", "External destination"]
    },
    explain_shap: {
      features: {
        "data_size": 0.52,
        "destination_ip": 0.41,
        "transfer_time": 0.28,
        "user_role": 0.15
      }
    },
    raw: {
      timestamp: "2024-01-15T11:45:23Z",
      user: "data_analyst@corp.com",
      destination: "external_ip:178.62.34.12",
      data_amount: "2.4GB",
      protocol: "HTTPS",
      duration: "45 minutes"
    },
    normalized: { data_size: "2.4GB", destination: "external_ip" }
  },
  "alert-004": {
    id: "alert-004",
    entity_id: "network-3345",
    entity_type: "network",
    event_type: "Port Scan",
    source: "NDR",
    detection_score: 0.712,
    ti_score: 0.589,
    correlation_score: 0.651,
    label: "problem",
    explain: {
      reason: "Multiple port scanning attempts detected from internal IP",
      confidence: "Medium",
      mitre_techniques: ["T1046"],
      risk_factors: ["Multiple ports", "Rapid scanning", "Internal source"]
    },
    explain_shap: {
      features: {
        "port_count": 0.48,
        "scan_rate": 0.37,
        "source_ip": 0.22,
        "time_window": 0.18
      }
    },
    raw: {
      timestamp: "2024-01-15T08:12:34Z",
      source_ip: "10.0.0.45",
      target_ip: "192.168.1.100",
      ports_scanned: "22,80,443,3389,8080",
      scan_duration: "2 minutes",
      packets_per_second: 45
    },
    normalized: { ports: "22,80,443", source_ip: "10.0.0.45" }
  },
  "alert-005": {
    id: "alert-005",
    entity_id: "user-1124",
    entity_type: "user",
    event_type: "Normal Login",
    source: "SIEM",
    detection_score: 0.123,
    ti_score: 0.045,
    correlation_score: 0.084,
    label: "normal",
    explain: {
      reason: "Normal login during business hours from known location",
      confidence: "High",
      note: "Expected user behavior"
    },
    explain_shap: {
      features: {
        "login_time": 0.05,
        "location": 0.03,
        "device": 0.02,
        "success_rate": 0.01
      }
    },
    raw: {
      timestamp: "2024-01-15T09:30:15Z",
      user: "employee@corp.com",
      ip: "192.168.1.50",
      location: "Office Building A",
      success: true,
      mfa_passed: true,
      department: "HR"
    },
    normalized: { location: "Internal", time_of_day: "09:30" }
  },
  "alert-006": {
    id: "alert-006",
    entity_id: "endpoint-5567",
    entity_type: "endpoint",
    event_type: "Config Drift",
    source: "Policy",
    detection_score: 0.456,
    ti_score: 0.231,
    correlation_score: 0.342,
    label: "problem",
    explain: {
      reason: "Firewall configuration changed from baseline",
      confidence: "Medium",
      mitre_techniques: ["T1562"],
      severity: "High",
      policy_violation: "Security policy breach"
    },
    explain_shap: {
      features: {
        "config_change": 0.38,
        "policy_violation": 0.31,
        "baseline_deviation": 0.24,
        "risk_level": 0.17
      }
    },
    raw: {
      timestamp: "2024-01-15T14:20:45Z",
      endpoint: "WS-5567",
      config_item: "Firewall Rules",
      old_value: "Enabled",
      new_value: "Disabled",
      policy: "SEC-POL-001",
      violation_type: "Security Control Disabled"
    },
    normalized: { policy_violation: "firewall_disabled", severity: "high" }
  },
  "alert-007": {
    id: "alert-007",
    entity_id: "user-8891",
    entity_type: "user",
    event_type: "Normal Activity",
    source: "UEBA",
    detection_score: 0.089,
    ti_score: 0.012,
    correlation_score: 0.051,
    label: "problem",
    explain: {
      reason: "Routine database access during working hours",
      confidence: "Low",
      note: "Potential false positive - normal work activity"
    },
    explain_shap: {
      features: {
        "time_of_day": 0.02,
        "access_pattern": 0.01,
        "data_amount": 0.005
      }
    },
    raw: {
      user: "analyst@corp.com",
      action: "database_query",
      time: "14:30",
      data_size: "1.2MB",
      query_type: "SELECT"
    },
    normalized: { activity: "routine_access", risk_score: "low" }
  },
  "alert-008": {
    id: "alert-008",
    entity_id: "network-7788",
    entity_type: "network",
    event_type: "DDoS Attack",
    source: "NDR",
    detection_score: 0.998,
    ti_score: 0.978,
    correlation_score: 0.988,
    label: "normal",
    explain: {
      reason: "Distributed Denial of Service attack detected",
      confidence: "Very High",
      severity: "Critical",
      mitigation: "Traffic filtering activated"
    },
    explain_shap: {
      features: {
        "packet_rate": 0.89,
        "source_diversity": 0.76,
        "traffic_pattern": 0.68,
        "duration": 0.54
      }
    },
    raw: {
      type: "UDP Flood",
      rate: "10 Gbps",
      sources: "1,200+ IPs",
      target: "web-server-01",
      duration: "15 minutes",
      mitigation: "active"
    },
    normalized: { traffic_rate: "10Gbps", duration: "15min" }
  }
};

const AlertsTable: React.FC<AlertsTableProps> = ({ onEntitySelected }) => {
  const [alerts, setAlerts] = useState<Alert[]>(DUMMY_ALERTS);
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>("alert-001");
  const [detail, setDetail] = useState<AlertDetail | null>(DUMMY_DETAILS["alert-001"]);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [labelFilter, setLabelFilter] = useState<"all" | "problem" | "normal">("all");
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<string | undefined>("user-8472");

  // Initialize with first alert selected
  useEffect(() => {
    if (alerts.length > 0 && !selectedId) {
      setSelectedId(alerts[0].id);
      setDetail(DUMMY_DETAILS[alerts[0].id]);
      const entity = alerts[0].entity_id;
      setSelectedEntity(entity);
      onEntitySelected?.(entity);
    }
  }, [alerts]);

  const filteredAlerts = alerts.filter((a) => {
    if (labelFilter === "all") return true;
    return (a.label || "") === labelFilter;
  });

  const handleRowClick = (a: Alert) => {
    setSelectedId(a.id);
    setDetail(DUMMY_DETAILS[a.id] || null);
    setSelectedEntity(a.entity_id);
    onEntitySelected?.(a.entity_id);
  };

  const handleFeedback = async (label: "problem" | "normal") => {
    if (!selectedId) return;
    try {
      setFeedbackLoading(true);
      setAlerts(prev => prev.map(alert => 
        alert.id === selectedId ? { ...alert, label } : alert
      ));
      if (detail) {
        setDetail({ ...detail, label });
      }
    } catch (e) {
      console.error("Failed to send feedback", e);
    } finally {
      setFeedbackLoading(false);
    }
  };

  return (
    <div className="alerts-layout">
      {/* Alerts list */ /*}
      <div className="alerts-list">
        <div className="alerts-toolbar">
          <div className="toolbar-title">
            <h3>Security Alerts</h3>
            <div className="alert-summary">
              <span className="total-count">{filteredAlerts.length} Alerts</span>
              <span className="problem-count">
                {filteredAlerts.filter(a => a.label === 'problem').length} Threats
              </span>
            </div>
          </div>
          <div className="alerts-filter">
            <div className="filter-group">
              <label className="filter-label">Filter:</label>
              <select
                value={labelFilter}
                onChange={(e) => setLabelFilter(e.target.value as any)}
                className="filter-select"
              >
                <option value="all">All Alerts</option>
                <option value="problem">Threats Only</option>
                <option value="normal">Normal Only</option>
              </select>
            </div>
            <button className="btn-refresh" onClick={() => setAlerts([...DUMMY_ALERTS])}>
              <span className="refresh-icon">↻</span>
              Refresh
            </button>
          </div>
        </div>

        <div className="alerts-table-container">
          <div className="table-header">
            <div className="header-cell entity">Entity</div>
            <div className="header-cell event">Event Type</div>
            <div className="header-cell source">Source</div>
            <div className="header-cell score">Threat Score</div>
            <div className="header-cell status">Status</div>
            <div className="header-cell time">Time</div>
          </div>
          <div className="table-body">
            {filteredAlerts.map((a) => {
              const active = selectedId === a.id;
              const isWrongData = a.id === "alert-007" || a.id === "alert-008";
              
              return (
                <div
                  key={a.id}
                  className={`table-row ${active ? 'active' : ''} ${isWrongData ? 'wrong-data' : ''}`}
                  onClick={() => handleRowClick(a)}
                >
                  <div className="table-cell entity">
                    <div className="entity-info">
                      <div className="entity-id">{a.entity_id}</div>
                      <div className="entity-type">{a.entity_type}</div>
                    </div>
                  </div>
                  <div className="table-cell event">
                    <div className="event-info">
                      <div className="event-type">{a.event_type}</div>
                      {isWrongData && <span className="warning-tag">⚠️ Check</span>}
                    </div>
                  </div>
                  <div className="table-cell source">
                    <span className={`source-badge source-${a.source?.toLowerCase()}`}>
                      {a.source}
                    </span>
                  </div>
                  <div className="table-cell score">
                    <div className="score-container">
                      <div className="score-value">
                        {(a.detection_score * 100).toFixed(1)}%
                      </div>
                      <div className="score-bar">
                        <div 
                          className="score-fill"
                          style={{ width: `${(a.detection_score || 0) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                  <div className="table-cell status">
                    <SeverityBadge label={a.label} />
                  </div>
                  <div className="table-cell time">
                    {a.alert_ts
                      ? new Date(a.alert_ts).toLocaleTimeString([], { 
                          hour: '2-digit', 
                          minute: '2-digit',
                          hour12: false 
                        })
                      : "-"}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Details & Sidebar */ /*}
      <div className="details-sidebar">
        {/* Alert Details */ /*}
        <div className="alert-investigation-card">
          <div className="investigation-header">
            <div className="header-content">
              <h3>Alert Investigation</h3>
              <b><span className="alert-id">{selectedId}</span></b>
            </div>
            <div className="header-actions">
              <button className="btn-export">📥 Export</button>
              <button className="btn-print">🖨️ Print</button>
            </div>
          </div>
          
          <div className="investigation-body">
            {!selectedId && (
              <div className="empty-investigation">
                <div className="empty-icon">🔍</div>
                <h4>Select an Alert to Investigate</h4>
                <p>Click on any alert in the table to view detailed information</p>
              </div>
            )}
            
            {selectedId && detail ? (
              <AlertDetails
                alert={detail}
                onFeedback={handleFeedback}
                feedbackLoading={feedbackLoading}
              />
            ) : selectedId ? (
              <div className="empty-investigation">
                <div className="empty-icon">📋</div>
                <h4>No Detailed Information</h4>
                <p>Detailed information is not available for this alert</p>
              </div>
            ) : null}
          </div>
        </div>

        {/* Correlation & Neighbors Panels */ /*}
        <div className="analysis-panels">
          <CorrelationPanel entityId={selectedEntity} />
          <NeighbourList entityId={selectedEntity} />
        </div>
      </div>
    </div>
  );
};

interface DetailsProps {
  alert: AlertDetail;
  onFeedback: (label: "problem" | "normal") => void;
  feedbackLoading: boolean;
}

const AlertDetails: React.FC<DetailsProps> = ({
  alert,
  onFeedback,
  feedbackLoading,
}) => {
  const {
    id,
    entity_id,
    entity_type,
    event_type,
    source,
    detection_score = 0,
    ti_score = 0,
    correlation_score = 0,
    label,
    explain,
    explain_shap,
    raw,
    normalized,
  } = alert;

  const isWrongData = id === "alert-007" || id === "alert-008";
  const scoreColor = (detection_score || 0) > 0.7 ? "#ef4444" : (detection_score || 0) > 0.4 ? "#f59e0b" : "#10b981";

  return (
    <div className="alert-details-container">
      {/* Alert Header */ /*}
      {isWrongData && (
        <div className="data-quality-warning">
          <div className="warning-icon">⚠️</div>
          <div className="warning-content">
            <strong>Data Quality Issue Detected</strong>
            <p>
              {id === "alert-007" && "Normal activity incorrectly flagged as problem."}
              {id === "alert-008" && "Critical threat incorrectly marked as normal."}
            </p>
          </div>
        </div>
      )}

      <div className="alert-header">
        <div className="header-main">
          <h2 className="alert-title">{event_type}</h2>
          <div className="alert-meta">
            <span className="meta-item">
              <span className="meta-label">Entity:</span>
              <span className="meta-value">{entity_id}</span>
            </span>
            <span className="meta-divider">•</span>
            <span className="meta-item">
              <span className="meta-label">Type:</span>
              <span className="meta-value">{entity_type}</span>
            </span>
          </div>
        </div>
        <div className="header-score">
          <div className="score-display" style={{ color: scoreColor }}>
            <div className="score-label">Threat Score</div>
            <div className="score-value">{((detection_score || 0) * 100).toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Quick Stats */ /*}
      <div className="quick-stats-grid">
        <div className="stat-card">
          <div className="stat-label">TI Score</div>
          <div className="stat-value">{ti_score != null ? ti_score.toFixed(3) : "-"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Correlation</div>
          <div className="stat-value">{correlation_score != null ? correlation_score.toFixed(3) : "-"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Source</div>
          <div className="stat-value source-tag">{source}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Status</div>
          <div className="stat-value"><SeverityBadge label={label} /></div>
        </div>
      </div>

      {/* Analyst Feedback */ /*}
      <div className="analyst-feedback-section">
        <div className="section-header">
          <h4>Analyst Feedback</h4>
          <span className="section-help">Help improve detection accuracy</span>
        </div>
        <div className="feedback-actions">
          <button
            className={`feedback-btn confirm-threat ${label === 'problem' ? 'active' : ''}`}
            disabled={feedbackLoading || label === 'problem'}
            onClick={() => onFeedback('problem')}
          >
            <span className="btn-icon">✅</span>
            <span className="btn-text">Confirm Threat</span>
          </button>
          <button
            className={`feedback-btn mark-normal ${label === 'normal' ? 'active' : ''}`}
            disabled={feedbackLoading || label === 'normal'}
            onClick={() => onFeedback('normal')}
          >
            <span className="btn-icon">🔄</span>
            <span className="btn-text">Mark as Normal</span>
          </button>
          <button className="feedback-btn secondary">
            <span className="btn-icon">🔍</span>
            <span className="btn-text">Investigate</span>
          </button>
        </div>
      </div>

      {/* AI Explanations */ /*}
      <div className="ai-analysis-section">
        <div className="section-header">
          <h4>AI Analysis</h4>
          <span className="section-badge">Powered by ML Models</span>
        </div>
        
        <div className="explanation-cards">
          <div className="explanation-card">
            <div className="card-header">
              <span className="card-title">Reasoning</span>
              <span className="card-badge">{explain?.confidence || "Unknown"}</span>
            </div>
            <div className="card-body">
              <p className="reason-text">{explain?.reason || "No explanation available"}</p>
              {explain?.mitre_techniques && (
                <div className="mitre-techniques">
                  <span className="mitre-label">MITRE Techniques:</span>
                  <div className="technique-tags">
                    {explain.mitre_techniques.map((tech, idx) => (
                      <span key={idx} className="technique-tag">{tech}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {explain_shap && (
            <div className="explanation-card">
              <div className="card-header">
                <span className="card-title">Feature Importance</span>
                <span className="card-badge">SHAP Analysis</span>
              </div>
              <div className="card-body">
                <div className="feature-importance-list">
                  {Object.entries(explain_shap.features || {}).map(([feature, importance]) => (
                    <div key={feature} className="feature-item">
                      <div className="feature-header">
                        <span className="feature-name">{feature.replace(/_/g, ' ')}</span>
                        <span className="feature-value">{(importance as number).toFixed(3)}</span>
                      </div>
                      <div className="feature-bar">
                        <div 
                          className="feature-importance-fill"
                          style={{ width: `${(importance as number) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Raw Data */ /*}
      <div className="raw-data-section">
        <div className="section-header">
          <h4>Raw Event Data</h4>
          <div className="data-format">
            <span className="format-tag active">JSON</span>
            <span className="format-tag">Text</span>
            <span className="format-tag">Hex</span>
          </div>
        </div>
        <div className="data-viewer">
          <pre className="json-viewer">
            {raw ? JSON.stringify(raw, null, 2) : "No raw data available"}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default AlertsTable; */
// src/components/AlertsTable.tsx
/* 
import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAlerts, getSeverity } from "../api/client";
import type { Alert } from "../types";
import SeverityBadge from "./SeverityBadge";

const AlertsTable: React.FC = () => {
  const { data = [], isLoading, isError } = useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 5000,
  });

  if (isLoading) return <div className="card">Loading Alerts…</div>;
  if (isError) return <div className="card error">Error Loading Alerts.</div>;

  const alerts = data as Alert[];

  return (
    <div className="card">
      <div className="card-header">
        <h3>Alerts</h3>
        <span className="badge">{alerts.length}</span>
      </div>

      <div className="table-wrapper">
        <table className="alerts-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Entity</th>
              <th>Event</th>
              <th>Source</th>
              <th>Det. Score</th>
              <th>Corr.</th>
              <th>Identifier</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 && (
              <tr>
                <td colSpan={9} style={{ textAlign: "center", padding: "1rem" }}>
                  No alerts yet – replay CloudTrail JSON to see detections.
                </td>
              </tr>
            )}
            {alerts.map((a) => {
              const sev = getSeverity(a);
              return (
                <tr key={String(a.id)}>
                  <td>{a.alert_ts ? new Date(a.alert_ts).toLocaleString() : "-"}</td>
                  <td>{a.entity_id ?? "-"}</td>
                  <td>{a.event_type ?? "-"}</td>
                  <td>{a.source ?? "-"}</td>
                  <td>{a.detection_score != null ? a.detection_score.toFixed(3) : "-"}</td>
                  <td>{a.correlation_score != null ? a.correlation_score.toFixed(3) : "-"}</td>
                  <td>{a.identifier_type ?? "-"}</td>
                  <td>
                    <span className={`severity-label ${sev}`}>{sev.toUpperCase()}</span> 
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AlertsTable; */


// src/components/AlertsTable.tsx
import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAlerts, getSeverity } from "../api/client";
import type { Alert } from "../types";
import identifierLabel from "./IdentifierLabel";

const AlertsTable: React.FC = () => {
  const { data = [], isLoading, isError } = useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 5000,
  });

  if (isLoading) return <div className="card">Loading alerts…</div>;
  if (isError) return <div className="card error">Error loading alerts.</div>;

  const alerts = (data || []) as Alert[];

  // try many possible IP keys
  function extractSourceIp(a: Alert) {
    const raw = (a as any).raw || (a as any).normalized || {};
    const candidates = [
      raw?.sourceIPAddress,
      raw?.source_ip,
      raw?.sourceIpAddress,
      raw?.source,
      a.source, // fallback (may be region)
    ];
    for (const c of candidates) {
      if (c && typeof c === "string" && c.trim() !== "") {
        // crude IP detect — if value contains letters it's probably a region; still return it
        return c;
      }
    }
    return "-";
  }

  // extract region from AWS fields or fall back to a.source (since your backend writes region into source)
  function extractRegion(a: Alert) {
    const raw = (a as any).raw || (a as any).normalized || {};
    const candidates = [
      raw?.awsRegion,
      raw?.aws_region,
      raw?.region,
      raw?.geo?.region,
      a.source,
    ];
    for (const c of candidates) {
      if (c && typeof c === "string" && c.trim() !== "") return c;
    }
    return "-";
  }

  // format entity (shorten ARNs)
  function formatEntity(entity?: string | null) {
    if (!entity) return "-";
    try {
      if (entity.includes("/")) {
        const parts = entity.split("/");
        return parts[parts.length - 1] || entity;
      }
      return entity;
    } catch {
      return entity;
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>Alerts</h3>
        <span className="badge">{alerts.length}</span>
      </div>

      <div className="table-wrapper">
        <table className="alerts-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Entity</th>
              <th>Event</th>
              <th>Source (IP)</th>
              <th>Region</th>
              <th>Det. Score</th>
              <th>Corr.</th>
              <th>Identifier</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 && (
              <tr>
                <td colSpan={9} style={{ textAlign: "center", padding: "1rem" }}>
                  No alerts yet – replay CloudTrail JSON to see detections.
                </td>
              </tr>
            )}

            {alerts.map((a) => {
              const sev = getSeverity(a);
              const srcIp = extractSourceIp(a);
              const region = extractRegion(a);
              const idLabel = identifierLabel(a.identifier_type || (a as any).identifier || "");
              const corr = a.correlation_score ?? 0;

              return (
                <tr key={String(a.id)}>
                  <td>{a.alert_ts ? new Date(String(a.alert_ts)).toLocaleString() : "-"}</td>
                  <td>{formatEntity(a.entity_id)}</td>
                  <td>{a.event_type ?? "-"}</td>
                  <td>{srcIp}</td>
                  <td>{region}</td>
                  <td>{typeof a.detection_score === "number" ? a.detection_score.toFixed(3) : "-"}</td>
                  <td>{typeof corr === "number" ? corr.toFixed(3) : "-"}</td>
                  <td>{idLabel}</td>
                  <td>
                    <span className={`severity-label ${sev}`}>{String(sev).toUpperCase()}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AlertsTable;

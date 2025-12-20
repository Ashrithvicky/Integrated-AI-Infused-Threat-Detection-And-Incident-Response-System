// src/api/client.ts
/* import axios from "axios";
import type {
  Alert,
  AlertDetail,
  CorrelationInfo,
  NeighborEdge,
} from "./types";

// Use Vite proxy (vite.config.ts) or change to full URLs if needed
const API_BASE = "/api";
const GRAPH_BASE = "/graph-api";

export async function fetchAlerts(): Promise<Alert[]> {
  const res = await axios.get(`${API_BASE}/alerts`);
  const data = res.data;

  // Try to coerce into an array safely
  if (Array.isArray(data)) {
    return data as Alert[];
  }
  if (data && Array.isArray(data.alerts)) {
    return data.alerts as Alert[];
  }

  console.warn("[fetchAlerts] Unexpected response shape:", data);
  return [];
}

export async function fetchAlert(alertId: string): Promise<AlertDetail> {
  const res = await axios.get(`${API_BASE}/alerts/${alertId}`);
  const data = res.data;

  // Either { ...alertFields } or { alert: { ... } }
  if (data && data.alert) {
    return data.alert as AlertDetail;
  }
  return data as AlertDetail;
}

export async function sendAlertFeedback(
  alertId: string,
  label: "problem" | "normal"
) {
  try {
    await axios.post(`${API_BASE}/alerts/feedback`, {
      alert_id: alertId,
      label,
    });
  } catch (e) {
    console.error("[sendAlertFeedback] error:", e);
    throw e;
  }
}

export async function fetchCorrelation(
  entityId: string
): Promise<CorrelationInfo> {
  const res = await axios.get(
    `${GRAPH_BASE}/correlate/${encodeURIComponent(entityId)}`
  );
  return res.data as CorrelationInfo;
}

export async function fetchNeighbors(entityId: string): Promise<{
  node: string;
  neighbors: NeighborEdge[];
}> {
  const res = await axios.get(
    `${GRAPH_BASE}/neighbors/${encodeURIComponent(entityId)}`
  );
  const data = res.data;
  if (!data || !Array.isArray(data.neighbors)) {
    console.warn("[fetchNeighbors] Unexpected response shape:", data);
    return { node: entityId, neighbors: [] };
  }
  return data as { node: string; neighbors: NeighborEdge[] };
}  */


// src/api/client.ts
import axios from "axios";
import type { Alert } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const api = axios.create({ baseURL: API_BASE_URL });



export async function fetchAlerts(): Promise<Alert[]> {
  const res = await api.get<Alert[]>("/alerts");
  console.log("[fetchAlerts] raw response:", res.data);
  return res.data || [];
}


// Prefer backend severity if present. Normalized mapping for UI.
export function getSeverity(alert: Alert): "low" | "medium" | "high" {
  if (alert.severity) {
    const s = String(alert.severity).toLowerCase();
    if (s === "high" || s === "h") return "high";
    if (s === "medium" || s === "med" || s === "m") return "medium";
    return "low";
  }
  // fallback: derive from detection_score
  const score = alert.detection_score ?? 0;
  if (score > 0.7) return "high";
  if (score >= 0.4) return "medium";
  return "low";
}


// src/api/client.ts
export async function fetchSystemHealth(): Promise<any> {
  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const res = await fetch(`${API_BASE_URL}/system-health`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

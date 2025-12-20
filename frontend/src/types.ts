// src/api/types.ts

/* export interface Alert {
  id: string
  event_id?: string
  entity_id?: string
  entity_type?: string
  event_type?: string
  source?: string
  detection_score?: number
  ti_score?: number
  correlation_score?: number
  label?: string
  alert_ts?: string
}

export interface AlertDetail extends Alert {
  raw?: any
  normalized?: any
  enriched?: any
  explain?: any
  explain_shap?: any
}

export interface CorrelationInfo {
  entity: string
  correlation_score: number
  neighbors: string[]
  attribution: number
}

export interface NeighborEdge {
  id: string
  edge?: {
    type?: string
    [key: string]: any
  }
} */

// src/types.ts
/* export type AlertLabel = "normal" | "problem" | string;

export interface Alert {
  id: number;
  event_id: string | null;
  entity_id: string | null;
  entity_type: string | null;/* /* 
  event_type: string | null;
  source: string | null;
  detection_score: number | null;
  ti_score: number | null;
  correlation_score: number | null;
  label: AlertLabel;
  alert_ts: string | null;
  explain?: unknown;
  explain_shap?: unknown;
  raw?: unknown;
  normalized?: unknown;
} */

// src/types.ts
export type AlertLabel = "normal" | "problem" | string;
export type Severity = "low" | "medium" | "high" | string;

export interface Alert {
  id: string;
  event_id?: string | null;
  entity_id?: string | null;
  entity_type?: string | null;
  event_type?: string | null;
  source?: string | null;
  detection_score?: number | null;
  ti_score?: number | null;
  correlation_score?: number | null;
  identifier_type?: string | null;
  severity?: Severity | null;
  label?: AlertLabel;
  alert_ts?: string | null;
  explain?: unknown;
  explain_shap?: unknown;
  raw?: unknown;
  normalized?: unknown;
}

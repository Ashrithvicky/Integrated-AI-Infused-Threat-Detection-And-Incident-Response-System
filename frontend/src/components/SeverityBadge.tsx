// src/components/SeverityBadge.tsx
import React from "react";

interface Props {
  score?: number;
  label?: "LOW" | "MEDIUM" | "HIGH" | string | undefined;
}

const SeverityBadge: React.FC<Props> = ({ score = 0, label }) => {
  const sev = (label as string) || (score >= 0.8 ? "HIGH" : score >= 0.4 ? "MEDIUM" : "LOW");
  const base = "px-2 py-1 rounded-full text-xs font-semibold inline-block";

  if (sev === "HIGH") return <span className={`${base}`} style={{ background: "#7f1d1d", color: "#fff" }}>HIGH</span>;
  if (sev === "MEDIUM") return <span className={`${base}`} style={{ background: "#92400e", color: "#fff" }}>MED</span>;
  if (sev === "LOW") return <span className={`${base}`} style={{ background: "#065f46", color: "#fff" }}>LOW</span>;
  return <span className={base} style={{ background: "#334155", color: "#fff" }}>{String(sev)}</span>;
};

export default SeverityBadge;

// src/components/identifierLabel.ts
export default function identifierLabel(idstr: string | undefined | null): string {
  if (!idstr) return "Fused";
  const s = String(idstr).toLowerCase();
  if (s.startsWith("rule:")) return "Rule";
  if (s.startsWith("graph:")) return "Graph";
  if (s.startsWith("ti:")) return "Threat Intel";
  if (s.startsWith("seq:")) return "Sequence";
  if (s.startsWith("ueba:")) return "UEBA";
  if (s.startsWith("fused:")) return "Fused";
  // unknown identifier, return original but pretty-cased
  return idstr;
}

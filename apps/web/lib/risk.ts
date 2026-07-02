/** Severity presentation helpers shared across pages. */

export function severityColor(sev: string): string {
  switch (sev) {
    case "Critical":
      return "#e02d3c";
    case "High":
      return "#f97316";
    case "Medium":
      return "#f59e0b";
    default:
      return "#22c55e";
  }
}

export function severityBadgeClass(sev: string): string {
  switch (sev) {
    case "Critical":
      return "bg-alert-600/15 text-alert-600 border-alert-600/40";
    case "High":
      return "bg-orange-500/15 text-orange-400 border-orange-500/40";
    case "Medium":
      return "bg-warn-500/15 text-warn-500 border-warn-500/40";
    default:
      return "bg-safe-500/15 text-safe-500 border-safe-500/40";
  }
}

export function scoreToSeverity(score: number): string {
  if (score >= 75) return "Critical";
  if (score >= 50) return "High";
  if (score >= 25) return "Medium";
  return "Low";
}

export function fmtCategory(cat: string): string {
  return cat.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

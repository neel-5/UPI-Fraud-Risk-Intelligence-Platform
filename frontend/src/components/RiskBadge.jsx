import { tierColor } from "../utils/formatters";

export default function RiskBadge({ tier, score }) {
  const color = tierColor(tier);
  return (
    <span className="risk-badge" style={{ "--badge-color": color }}>
      <span className="risk-dot" />
      {tier}
      {typeof score === "number" ? <strong>{Math.round(score)}</strong> : null}
    </span>
  );
}

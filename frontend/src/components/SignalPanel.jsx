import { Activity, Cpu, GitBranch, Landmark, Network } from "lucide-react";
import RiskBadge from "./RiskBadge";
import { formatMoney } from "../utils/formatters";

const icons = [Activity, Network, GitBranch, Cpu, Landmark];

export default function SignalPanel({ account }) {
  if (!account) {
    return (
      <section className="panel">
        <div className="empty-state">Select an account to inspect risk signals.</div>
      </section>
    );
  }

  const metrics = account.metrics;

  return (
    <section className="panel signal-panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Account Detail</p>
          <h2>{account.account.vpa}</h2>
        </div>
        <RiskBadge tier={account.risk_tier} score={account.risk_score} />
      </div>

      <div className="metric-grid mini">
        <div>
          <span>Sent</span>
          <strong>{formatMoney(metrics.sent_amount)}</strong>
        </div>
        <div>
          <span>Received</span>
          <strong>{formatMoney(metrics.received_amount)}</strong>
        </div>
        <div>
          <span>Neighbors</span>
          <strong>{metrics.unique_neighbors}</strong>
        </div>
        <div>
          <span>Burst</span>
          <strong>{metrics.hourly_burst}/hr</strong>
        </div>
      </div>

      <div className="signals">
        {account.signals.map((signal, index) => {
          const Icon = icons[index % icons.length];
          return (
            <article className="signal-row" key={signal.name}>
              <div className="signal-icon">
                <Icon size={18} />
              </div>
              <div>
                <div className="signal-topline">
                  <strong>{signal.name}</strong>
                  <span>{signal.contribution}</span>
                </div>
                <p>{signal.explanation}</p>
                <div className="signal-bar">
                  <span style={{ width: `${Math.min(100, signal.value * 100)}%` }} />
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

import { useState } from "react";
import { Play, ShieldAlert } from "lucide-react";
import RiskBadge from "./RiskBadge";

const channels = ["UPI_APP", "QR_SCAN", "COLLECT_REQUEST", "PAYMENT_LINK", "WEB_CHECKOUT"];

export default function SimulationPanel({ accounts, onSimulate, result, loading }) {
  const [form, setForm] = useState({
    sender_id: "ACC0019",
    receiver_id: "ACC0115",
    amount: 24500,
    channel: "PAYMENT_LINK",
    city: "Mumbai",
    device_id: "DEV-NEW-1"
  });

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({
      ...current,
      [name]: name === "amount" ? Number(value) : value
    }));
  }

  function submit(event) {
    event.preventDefault();
    onSimulate(form);
  }

  return (
    <section className="panel simulator-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Real-time Scoring</p>
          <h2>Payment Simulator</h2>
        </div>
        <ShieldAlert size={22} />
      </div>

      <form className="simulator-form" onSubmit={submit}>
        <label>
          Sender
          <select name="sender_id" value={form.sender_id} onChange={updateField}>
            {accounts.map((row) => (
              <option key={row.account.account_id} value={row.account.account_id}>
                {row.account.account_id} · {row.account.vpa}
              </option>
            ))}
          </select>
        </label>
        <label>
          Receiver
          <select name="receiver_id" value={form.receiver_id} onChange={updateField}>
            {accounts.map((row) => (
              <option key={row.account.account_id} value={row.account.account_id}>
                {row.account.account_id} · {row.account.vpa}
              </option>
            ))}
          </select>
        </label>
        <label>
          Amount
          <input name="amount" type="number" min="1" value={form.amount} onChange={updateField} />
        </label>
        <label>
          Channel
          <select name="channel" value={form.channel} onChange={updateField}>
            {channels.map((channel) => (
              <option key={channel} value={channel}>
                {channel}
              </option>
            ))}
          </select>
        </label>
        <label>
          City
          <input name="city" value={form.city} onChange={updateField} />
        </label>
        <label>
          Device
          <input name="device_id" value={form.device_id} onChange={updateField} />
        </label>
        <button className="primary-button" disabled={loading} type="submit" title="Score payment">
          <Play size={17} />
          {loading ? "Scoring" : "Score"}
        </button>
      </form>

      {result ? (
        <div className="simulation-result">
          <div>
            <span>Decision</span>
            <strong>{result.decision}</strong>
          </div>
          <RiskBadge tier={result.risk_tier} score={result.risk_score} />
          <div className="reason-grid">
            {result.reasons.map((reason) => (
              <span key={reason.label}>
                {reason.label}
                <strong>{reason.value}</strong>
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

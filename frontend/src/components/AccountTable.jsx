import { ChevronRight } from "lucide-react";
import RiskBadge from "./RiskBadge";
import { formatMoney, shortId } from "../utils/formatters";

export default function AccountTable({ accounts, selectedId, onSelect }) {
  return (
    <section className="panel account-table-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Prioritized Accounts</p>
          <h2>Risk Queue</h2>
        </div>
      </div>
      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>Account</th>
              <th>Type</th>
              <th>Tier</th>
              <th>Exposure</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {accounts.map((row) => (
              <tr
                key={row.account.account_id}
                className={selectedId === row.account.account_id ? "selected" : ""}
                onClick={() => onSelect(row.account.account_id)}
              >
                <td>
                  <strong>{shortId(row.account.account_id)}</strong>
                  <span>{row.account.vpa}</span>
                </td>
                <td>{row.account.account_type}</td>
                <td>
                  <RiskBadge tier={row.risk_tier} score={row.risk_score} />
                </td>
                <td>{formatMoney(row.metrics.sent_amount + row.metrics.received_amount)}</td>
                <td>
                  <button title="View account" className="icon-button" type="button">
                    <ChevronRight size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

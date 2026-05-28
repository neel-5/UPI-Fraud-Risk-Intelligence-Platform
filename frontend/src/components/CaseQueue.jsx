import { FileSearch } from "lucide-react";
import RiskBadge from "./RiskBadge";

export default function CaseQueue({ cases }) {
  return (
    <section className="panel cases-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Investigation</p>
          <h2>Open Cases</h2>
        </div>
      </div>
      <div className="case-list">
        {cases.map((item) => (
          <article className="case-item" key={item.case_id}>
            <div className="case-icon">
              <FileSearch size={18} />
            </div>
            <div>
              <div className="case-title">
                <strong>{item.case_id}</strong>
                <RiskBadge tier={item.priority} />
              </div>
              <p>{item.summary}</p>
              <span>
                {item.vpa} · {item.status} · {item.assigned_to}
              </span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

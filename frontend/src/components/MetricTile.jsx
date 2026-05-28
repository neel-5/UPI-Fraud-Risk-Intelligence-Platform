export default function MetricTile({ icon: Icon, label, value, footer, tone = "green" }) {
  return (
    <section className={`metric-tile tone-${tone}`}>
      <div className="metric-icon">{Icon ? <Icon size={20} /> : null}</div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        {footer ? <span>{footer}</span> : null}
      </div>
    </section>
  );
}

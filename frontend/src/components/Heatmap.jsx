export default function Heatmap({ data }) {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const max = Math.max(...data.map((item) => item.count), 1);
  const lookup = new Map(data.map((item) => [`${item.day}-${item.hour}`, item.count]));

  return (
    <section className="panel heatmap-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Temporal Signals</p>
          <h2>Transaction Heatmap</h2>
        </div>
      </div>
      <div className="heatmap">
        <div className="heatmap-hours">
          {[0, 6, 12, 18, 23].map((hour) => (
            <span key={hour}>{hour}:00</span>
          ))}
        </div>
        {days.map((day) => (
          <div className="heatmap-row" key={day}>
            <span>{day}</span>
            <div className="heatmap-cells">
              {Array.from({ length: 24 }, (_, hour) => {
                const count = lookup.get(`${day}-${hour}`) || 0;
                return (
                  <i
                    key={hour}
                    title={`${day} ${hour}:00 - ${count} transactions`}
                    style={{ opacity: 0.12 + (count / max) * 0.88 }}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

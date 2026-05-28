import { useMemo } from "react";
import { Network } from "lucide-react";
import { shortId, tierColor } from "../utils/formatters";

function buildLayout(nodes) {
  const width = 760;
  const height = 470;
  const centerX = width / 2;
  const centerY = height / 2;
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));

  return nodes.reduce((acc, node, index) => {
    const riskPull = (100 - node.risk_score) / 100;
    const radius = 55 + riskPull * 175 + (index % 5) * 10;
    const angle = index * goldenAngle;
    acc[node.id] = {
      ...node,
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
      r: 5 + Math.max(1, node.risk_score) / 13
    };
    return acc;
  }, {});
}

export default function NetworkGraph({ graph, selectedId, onSelect }) {
  const layout = useMemo(() => buildLayout(graph.nodes || []), [graph.nodes]);
  const nodes = Object.values(layout);
  const links = (graph.links || []).filter((link) => layout[link.source] && layout[link.target]);

  return (
    <section className="panel graph-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Network Intelligence</p>
          <h2>UPI Transaction Graph</h2>
        </div>
        <div className="panel-chip">
          <Network size={16} />
          {nodes.length} nodes · {links.length} links
        </div>
      </div>

      <div className="graph-stage">
        <svg viewBox="0 0 760 470" role="img" aria-label="UPI account graph">
          <defs>
            <filter id="nodeGlow">
              <feGaussianBlur stdDeviation="3.5" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <g className="links">
            {links.map((link) => {
              const source = layout[link.source];
              const target = layout[link.target];
              const risky = link.fraud_count > 0;
              return (
                <line
                  key={`${link.source}-${link.target}`}
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={risky ? "#e15554" : "#9fb0bf"}
                  strokeOpacity={risky ? 0.58 : 0.22}
                  strokeWidth={Math.min(5, 0.9 + link.count * 0.25)}
                />
              );
            })}
          </g>
          <g className="nodes">
            {nodes.map((node) => {
              const selected = selectedId === node.id;
              return (
                <g
                  key={node.id}
                  className="graph-node"
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={() => onSelect(node.id)}
                >
                  <circle
                    r={node.r + (selected ? 5 : 0)}
                    fill={tierColor(node.risk_tier)}
                    fillOpacity={selected ? 0.24 : 0.14}
                    stroke={tierColor(node.risk_tier)}
                    strokeWidth={selected ? 3 : 1.5}
                    filter={selected ? "url(#nodeGlow)" : undefined}
                  />
                  <circle r={Math.max(3, node.r * 0.45)} fill={tierColor(node.risk_tier)} />
                  {selected || node.risk_tier === "Critical" ? (
                    <text x={node.r + 8} y="4">
                      {shortId(node.id)}
                    </text>
                  ) : null}
                  <title>
                    {node.label} · {node.risk_tier} · {Math.round(node.risk_score)}
                  </title>
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      <div className="graph-legend">
        {["Critical", "High", "Medium", "Low"].map((tier) => (
          <span key={tier}>
            <i style={{ background: tierColor(tier) }} />
            {tier}
          </span>
        ))}
      </div>
    </section>
  );
}

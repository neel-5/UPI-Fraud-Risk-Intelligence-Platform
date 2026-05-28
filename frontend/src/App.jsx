import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  Database,
  IndianRupee,
  RefreshCw,
  ShieldCheck,
  UsersRound
} from "lucide-react";
import { api } from "./api/client";
import AccountTable from "./components/AccountTable";
import CaseQueue from "./components/CaseQueue";
import Heatmap from "./components/Heatmap";
import MetricTile from "./components/MetricTile";
import NetworkGraph from "./components/NetworkGraph";
import SignalPanel from "./components/SignalPanel";
import SimulationPanel from "./components/SimulationPanel";
import { formatMoney, formatNumber } from "./utils/formatters";

export default function App() {
  const [overview, setOverview] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [heatmap, setHeatmap] = useState([]);
  const [cases, setCases] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simLoading, setSimLoading] = useState(false);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [overviewData, accountData, graphData, heatmapData, caseData] = await Promise.all([
        api.overview(),
        api.accounts({ limit: 80 }),
        api.graph({ limit: 95, minimum_score: 18 }),
        api.heatmap(),
        api.cases()
      ]);
      setOverview(overviewData);
      setAccounts(accountData);
      setGraph(graphData);
      setHeatmap(heatmapData);
      setCases(caseData);
      setSelectedId((current) => current || accountData[0]?.account.account_id || null);
      setError("");
    } catch (requestError) {
      setError(`Dashboard API unavailable: ${requestError.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (!selectedId) return;
    api
      .account(selectedId)
      .then((accountData) => {
        setSelectedAccount(accountData);
        setError("");
      })
      .catch((requestError) => setError(`Account detail unavailable: ${requestError.message}`));
  }, [selectedId]);

  async function runSimulation(payload) {
    setSimLoading(true);
    setError("");
    try {
      const result = await api.simulate(payload);
      setSimulation(result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSimLoading(false);
    }
  }

  if (loading && !overview) {
    return (
      <main className="app-shell loading-shell">
        <div className="loading-mark" />
        <p>Loading risk graph</p>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Param Saxena · Final Year CSE Data Science</p>
          <h1>Graph-Based UPI Fraud Detection & Risk Intelligence</h1>
        </div>
        <button className="secondary-button" onClick={loadDashboard} type="button" title="Refresh dashboard">
          <RefreshCw size={17} />
          Refresh
        </button>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="metric-grid">
        <MetricTile
          icon={UsersRound}
          label="Accounts"
          value={formatNumber(overview?.total_accounts)}
          footer={`${formatNumber(overview?.high_risk_accounts)} high risk`}
          tone="green"
        />
        <MetricTile
          icon={Database}
          label="Transactions"
          value={formatNumber(overview?.total_transactions)}
          footer={`${Math.round((overview?.fraud_transaction_rate || 0) * 100)}% flagged seed rate`}
          tone="blue"
        />
        <MetricTile
          icon={IndianRupee}
          label="Network Volume"
          value={formatMoney(overview?.total_volume)}
          footer="Synthetic UPI graph"
          tone="gold"
        />
        <MetricTile
          icon={AlertTriangle}
          label="Critical Accounts"
          value={formatNumber(overview?.critical_accounts)}
          footer={`Largest component: ${formatNumber(overview?.largest_component_size)}`}
          tone="red"
        />
      </section>

      <section className="main-grid">
        <NetworkGraph graph={graph} selectedId={selectedId} onSelect={setSelectedId} />
        <SignalPanel account={selectedAccount} />
      </section>

      <section className="operations-grid">
        <AccountTable accounts={accounts} selectedId={selectedId} onSelect={setSelectedId} />
        <SimulationPanel
          accounts={accounts}
          onSimulate={runSimulation}
          result={simulation}
          loading={simLoading}
        />
      </section>

      <section className="bottom-grid">
        <Heatmap data={heatmap} />
        <CaseQueue cases={cases} />
      </section>

      <footer>
        <ShieldCheck size={16} />
        Explainable graph scoring · deterministic seed data · FastAPI + React
      </footer>
    </main>
  );
}

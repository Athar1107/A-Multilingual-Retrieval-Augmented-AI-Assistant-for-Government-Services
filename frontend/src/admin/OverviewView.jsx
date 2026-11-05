import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";

const ROUTE_COLORS = {
  direct: "#10b981",
  fallback_recovered: "#06b6d4",
  fallback_failed: "#f43f5e",
  unknown: "#94a3b8",
};

export default function OverviewView({ adminKey, onUnauthorized }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  async function loadOverview() {
    try {
      setLoading(true);
      setError("");
      const res = await fetch("/admin/overview", {
        headers: { "X-Admin-Key": adminKey },
      });
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (!res.ok) {
        throw new Error(`Failed to load overview telemetry (HTTP ${res.status})`);
      }
      const json = await res.json();
      setData(json);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err.message || "Failed to load telemetry data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOverview();
    const interval = setInterval(loadOverview, 15000);
    return () => clearInterval(interval);
  }, [adminKey]);

  if (loading && !data) {
    return (
      <div className="admin-loading-view" aria-busy="true">
        <div className="skeleton-line" style={{ width: "40%", height: 28 }} />
        <div className="kpi-grid" style={{ marginTop: 20 }}>
          {[...Array(6)].map((_, i) => (
            <div key={i} className="kpi-card">
              <div className="skeleton-line" style={{ width: "50%" }} />
              <div className="skeleton-line" style={{ width: "70%", height: 32 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">⚠️</div>
        <div className="empty-state-title">Telemetry Unavailable</div>
        <div className="empty-state-sub">{error}</div>
        <button type="button" className="retry-btn" onClick={loadOverview}>
          Retry Connection
        </button>
      </div>
    );
  }

  const routeData = Object.entries(data?.route_distribution || {}).map(([key, count]) => ({
    name: key.replace("_", " "),
    value: count,
    key,
  }));

  const stageLatencyData = [
    { stage: "Translate In", latency: data?.avg_stage_latency_ms?.translate_in || 0 },
    { stage: "Retrieve (Hybrid)", latency: data?.avg_stage_latency_ms?.retrieve || 0 },
    { stage: "Generate (LLM)", latency: data?.avg_stage_latency_ms?.generate || 0 },
    { stage: "Translate Out", latency: data?.avg_stage_latency_ms?.translate_out || 0 },
  ];

  const queriesPerHourData = (data?.queries_per_hour || []).map((q) => ({
    time: new Date(q.ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    queries: q.count,
  }));

  const histogramData = (data?.confidence_histogram || []).map((h) => ({
    range: `${h.bucket.toFixed(1)}-${(h.bucket + 0.1).toFixed(1)}`,
    queries: h.count,
  }));

  return (
    <div className="overview-container" role="region" aria-label="System Overview Telemetry">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>System &amp; RAG Telemetry</h2>
          <span style={{ fontSize: 12, color: "var(--admin-text-muted)" }}>
            Live status from active SQLite query ledger and ChromaDB index
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {lastUpdated && (
            <span style={{ fontSize: 11, color: "var(--admin-text-muted)" }}>
              Auto-refreshing (15s) • Last: {lastUpdated}
            </span>
          )}
          <button type="button" className="pagination-btn" onClick={loadOverview} aria-label="Refresh telemetry">
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card accent">
          <span className="kpi-label">Total Queries</span>
          <span className="kpi-value">{data?.total_queries?.toLocaleString() ?? 0}</span>
          <span className="kpi-subtext">{data?.queries_24h ?? 0} in past 24 hours</span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Average Latency</span>
          <span className="kpi-value">
            {data?.avg_latency_ms ? `${Math.round(data.avg_latency_ms)} ms` : "N/A"}
          </span>
          <span className="kpi-subtext">
            p95: {data?.p95_latency_ms ? `${Math.round(data.p95_latency_ms)} ms` : "N/A"}
          </span>
        </div>

        <div className="kpi-card ok">
          <span className="kpi-label">Average Confidence</span>
          <span className="kpi-value">
            {data?.avg_confidence != null ? `${(data.avg_confidence * 100).toFixed(1)}%` : "N/A"}
          </span>
          <span className="kpi-subtext">Empirical separation: 50.0%</span>
        </div>

        <div className="kpi-card warn">
          <span className="kpi-label">Fallback Rate</span>
          <span className="kpi-value">
            {data?.fallback_rate != null ? `${(data.fallback_rate * 100).toFixed(1)}%` : "0.0%"}
          </span>
          <span className="kpi-subtext">IndicTrans2 / Refusal routes</span>
        </div>

        <div className="kpi-card err">
          <span className="kpi-label">Error Rate</span>
          <span className="kpi-value">
            {data?.error_rate != null ? `${(data.error_rate * 100).toFixed(1)}%` : "0.0%"}
          </span>
          <span className="kpi-subtext">Pipeline failures</span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Active Corpus</span>
          <span className="kpi-value">{data?.corpus_chunks ?? 0}</span>
          <span className="kpi-subtext">{data?.corpus_documents ?? 0} verified documents</span>
        </div>
      </div>

      {/* Charts 2x2 Grid */}
      <div className="charts-grid">
        {/* Chart 1: Queries / Hour */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Query Velocity (Past 24 Hours)</span>
          </div>
          <div className="chart-container">
            {queriesPerHourData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={queriesPerHourData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", color: "#f8fafc" }}
                  />
                  <Line type="monotone" dataKey="queries" stroke="#06b6d4" strokeWidth={2.5} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state" style={{ padding: "40px 0" }}>
                <span>No query volume in the past 24 hours</span>
              </div>
            )}
          </div>
          <p className="chart-text-summary" aria-label="Text summary of query velocity">
            <strong>Summary:</strong> Shows requests logged per hourly bucket over the last 24-hour cycle.
          </p>
        </div>

        {/* Chart 2: Route Donut */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Routing Decisions</span>
          </div>
          <div className="chart-container">
            {routeData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={routeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {routeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={ROUTE_COLORS[entry.key] || "#94a3b8"} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", color: "#f8fafc" }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state" style={{ padding: "40px 0" }}>
                <span>No route data recorded yet</span>
              </div>
            )}
          </div>
          <p className="chart-text-summary" aria-label="Text summary of routing distribution">
            <strong>Summary:</strong> Distribution across direct scheme matches, fallback recovered queries, and refusal decisions.
          </p>
        </div>

        {/* Chart 3: Stage Latencies */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Average Latency per Pipeline Stage (ms)</span>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stageLatencyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="stage" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", color: "#f8fafc" }}
                />
                <Bar dataKey="latency" fill="#0891b2" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="chart-text-summary" aria-label="Text summary of stage latencies">
            <strong>Summary:</strong> Dissects latency into inbound translation, dense+BM25 retrieval, LLM synthesis, and outbound translation.
          </p>
        </div>

        {/* Chart 4: Confidence Histogram */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Confidence Score Distribution</span>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histogramData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="range" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", color: "#f8fafc" }}
                />
                <Bar dataKey="queries" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="chart-text-summary" aria-label="Text summary of confidence histogram">
            <strong>Summary:</strong> Groups citizen query confidence scores into 10 deciles (0.0 to 1.0).
          </p>
        </div>
      </div>
    </div>
  );
}


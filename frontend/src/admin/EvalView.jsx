import { useEffect, useState } from "react";

export default function EvalView({ adminKey, onUnauthorized }) {
  const [runs, setRuns] = useState([]);
  const [selectedRunName, setSelectedRunName] = useState("");
  const [selectedRunDetail, setSelectedRunDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Side-by-side comparison state
  const [compareMode, setCompareMode] = useState(false);
  const [runA, setRunA] = useState("");
  const [runB, setRunB] = useState("");
  const [detailA, setDetailA] = useState(null);
  const [detailB, setDetailB] = useState(null);

  async function loadRuns() {
    try {
      setLoading(true);
      setError("");
      const res = await fetch("/admin/eval/runs", {
        headers: { "X-Admin-Key": adminKey },
      });
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (!res.ok) {
        throw new Error(`Failed to load evaluation runs (HTTP ${res.status})`);
      }
      const json = await res.json();
      setRuns(json || []);
      if (json?.length) {
        setSelectedRunName(json[0].name);
        setRunA(json[0].name);
        if (json.length > 1) setRunB(json[1].name);
      }
    } catch (err) {
      setError(err.message || "Failed to load runs.");
    } finally {
      setLoading(false);
    }
  }

  async function loadRunDetail(name, setter) {
    if (!name) return;
    try {
      const res = await fetch(`/admin/eval/runs/${encodeURIComponent(name)}`, {
        headers: { "X-Admin-Key": adminKey },
      });
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (res.ok) {
        const json = await res.json();
        setter(json);
      }
    } catch {}
  }

  useEffect(() => {
    loadRuns();
  }, [adminKey]);

  useEffect(() => {
    if (selectedRunName && !compareMode) {
      loadRunDetail(selectedRunName, setSelectedRunDetail);
    }
  }, [selectedRunName, compareMode]);

  useEffect(() => {
    if (compareMode) {
      loadRunDetail(runA, setDetailA);
      loadRunDetail(runB, setDetailB);
    }
  }, [compareMode, runA, runB]);

  const scorerVersionsDiffer =
    compareMode &&
    detailA?.scorer_version &&
    detailB?.scorer_version &&
    detailA.scorer_version !== detailB.scorer_version;

  return (
    <div className="eval-container" role="region" aria-label="Evaluation Runs">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>Evaluation &amp; Accuracy Ledger</h2>
          <span style={{ fontSize: 12, color: "var(--admin-text-muted)" }}>
            Empirical benchmark runs from <code>backend/eval/results_*.json</code>
          </span>
        </div>
        <button
          type="button"
          className="pagination-btn"
          onClick={() => setCompareMode(!compareMode)}
        >
          {compareMode ? "← View Single Run" : "⇄ Side-by-Side Compare"}
        </button>
      </div>

      {loading ? (
        <div style={{ padding: 24 }}>
          {[...Array(3)].map((_, i) => (
            <div key={i} className="skeleton-line" style={{ height: 40, marginBottom: 12 }} />
          ))}
        </div>
      ) : error ? (
        <div className="empty-state">
          <div className="empty-state-title">Failed to load evaluations</div>
          <div className="empty-state-sub">{error}</div>
        </div>
      ) : compareMode ? (
        /* Side by Side Comparison */
        <div>
          <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Run A:</label>
              <select className="admin-select" style={{ width: "100%" }} value={runA} onChange={(e) => setRunA(e.target.value)}>
                {runs.map((r) => (
                  <option key={r.name} value={r.name}>{r.name} ({r.scorer_version})</option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Run B:</label>
              <select className="admin-select" style={{ width: "100%" }} value={runB} onChange={(e) => setRunB(e.target.value)}>
                {runs.map((r) => (
                  <option key={r.name} value={r.name}>{r.name} ({r.scorer_version})</option>
                ))}
              </select>
            </div>
          </div>

          {scorerVersionsDiffer && (
            <div
              style={{
                padding: "12px 18px",
                background: "rgba(245, 158, 11, 0.15)",
                border: "1px solid var(--admin-warn)",
                color: "var(--admin-warn)",
                borderRadius: 8,
                marginBottom: 20,
                fontSize: 13,
                fontWeight: 600,
              }}
              role="alert"
            >
              ⚠️ Warning: Scorer versions differ between these runs ({detailA?.scorer_version} vs {detailB?.scorer_version}). Direct numeric comparison may not be mathematically calibrated.
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            {/* Run A Summary */}
            <div className="kpi-card">
              <span className="kpi-label">Run A: {runA}</span>
              <p style={{ margin: "4px 0", fontSize: 13 }}>Scorer Version: <strong>{detailA?.scorer_version}</strong></p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>Total Questions: <strong>{detailA?.summary?.total || 0}</strong></p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>Passed: <strong>{detailA?.summary?.passed || 0}</strong></p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>
                Pass Rate: <strong>{detailA?.summary?.pass_rate != null ? `${(detailA.summary.pass_rate * 100).toFixed(1)}%` : "N/A"}</strong>
              </p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>
                Avg Relevance: <strong>{detailA?.summary?.avg_answer_relevance ?? "N/A"}</strong>
              </p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>
                Source Accuracy: <strong>{detailA?.summary?.source_accuracy != null ? `${(detailA.summary.source_accuracy * 100).toFixed(1)}%` : "N/A"}</strong>
              </p>
            </div>

            {/* Run B Summary */}
            <div className="kpi-card">
              <span className="kpi-label">Run B: {runB}</span>
              <p style={{ margin: "4px 0", fontSize: 13 }}>Scorer Version: <strong>{detailB?.scorer_version}</strong></p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>Total Questions: <strong>{detailB?.summary?.total || 0}</strong></p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>Passed: <strong>{detailB?.summary?.passed || 0}</strong></p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>
                Pass Rate: <strong>{detailB?.summary?.pass_rate != null ? `${(detailB.summary.pass_rate * 100).toFixed(1)}%` : "N/A"}</strong>
              </p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>
                Avg Relevance: <strong>{detailB?.summary?.avg_answer_relevance ?? "N/A"}</strong>
              </p>
              <p style={{ margin: "4px 0", fontSize: 13 }}>
                Source Accuracy: <strong>{detailB?.summary?.source_accuracy != null ? `${(detailB.summary.source_accuracy * 100).toFixed(1)}%` : "N/A"}</strong>
              </p>
            </div>
          </div>
        </div>
      ) : (
        /* Single Run View */
        <div>
          {/* Run Selection Tiles */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 14, marginBottom: 20 }}>
            {runs.map((r) => (
              <div
                key={r.name}
                className={`kpi-card ${selectedRunName === r.name ? "accent" : ""}`}
                style={{ cursor: "pointer", borderColor: selectedRunName === r.name ? "var(--admin-accent)" : "var(--admin-border)" }}
                onClick={() => setSelectedRunName(r.name)}
                tabIndex={0}
                role="button"
              >
                <span className="kpi-label">{r.name}</span>
                <span className="kpi-value" style={{ fontSize: 20 }}>
                  {r.summary?.pass_rate != null ? `${(r.summary.pass_rate * 100).toFixed(1)}%` : "N/A"}
                </span>
                <span className="kpi-subtext">
                  {r.summary?.passed || 0}/{r.summary?.total || 0} passed • {r.scorer_version}
                </span>
              </div>
            ))}
          </div>

          {/* Per-Question Details Table */}
          {selectedRunDetail && (
            <div className="table-card">
              <div className="table-controls">
                <span style={{ fontSize: 14, fontWeight: 700 }}>
                  Per-Question Results ({selectedRunDetail.results?.length || 0} tests)
                </span>
                <span className="badge ok">Scorer: {selectedRunDetail.scorer_version}</span>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Query</th>
                      <th>Expected Route</th>
                      <th>Actual Route</th>
                      <th>Confidence</th>
                      <th>Relevance</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(selectedRunDetail.results || []).map((q, idx) => (
                      <tr key={idx}>
                        <td>{idx + 1}</td>
                        <td style={{ maxWidth: 300 }}>{q.query}</td>
                        <td><span className="badge">{q.expected_route}</span></td>
                        <td><span className={`badge ${q.actual_route}`}>{q.actual_route}</span></td>
                        <td>{q.confidence != null ? `${(q.confidence * 100).toFixed(1)}%` : "—"}</td>
                        <td>{q.answer_relevance != null ? q.answer_relevance.toFixed(2) : "—"}</td>
                        <td>
                          <span className={`badge ${q.passed ? "ok" : "err"}`}>
                            {q.passed ? "PASS" : "FAIL"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


import { useState } from "react";

export default function TestConsoleView({ adminKey, onUnauthorized }) {
  const [queryText, setQueryText] = useState("");
  const [language, setLanguage] = useState("auto");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleExecute(e) {
    e?.preventDefault();
    if (!queryText.trim() || loading) return;

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const payload = {
        text: queryText.trim(),
        language: language === "auto" ? null : language,
      };

      const res = await fetch("/admin/debug/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Key": adminKey,
        },
        body: JSON.stringify(payload),
      });

      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Pipeline debug failed (HTTP ${res.status})`);
      }

      const json = await res.json();
      setResult(json);
    } catch (err) {
      setError(err.message || "Failed to execute debug query.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="test-console-container" role="region" aria-label="Test Console">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>RAG Pipeline Test Console</h2>
        <span style={{ fontSize: 12, color: "var(--admin-text-muted)" }}>
          Run real queries with detailed stage latency, hybrid dense+sparse score inspection, and routing traces.
          Queries executed here are marked with <code>source="admin"</code> and excluded from citizen statistics.
        </span>
      </div>

      {/* Input Card */}
      <form className="table-card" style={{ padding: 20, marginBottom: 24 }} onSubmit={handleExecute}>
        <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 700, marginBottom: 6 }}>
              Query Prompt (English or Goan Konkani):
            </label>
            <input
              type="text"
              style={{
                width: "100%",
                background: "var(--admin-bg)",
                border: "1px solid var(--admin-border)",
                color: "var(--admin-text-main)",
                padding: "10px 14px",
                borderRadius: 6,
                fontSize: 14,
                outline: "none",
              }}
              placeholder="e.g. How many scholarships under STSE in Goa each year? or पीएम शिष्यवृत्ती योजनेंत..."
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div style={{ width: 180 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 700, marginBottom: 6 }}>
              Language:
            </label>
            <select
              className="admin-select"
              style={{ width: "100%", padding: "10px 12px" }}
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={loading}
            >
              <option value="auto">Auto-detect Script</option>
              <option value="en">English (en)</option>
              <option value="kok">Goan Konkani (kok)</option>
            </select>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              className="pagination-btn"
              onClick={() => setQueryText("What is the PM scholarship benefit amount for boys and girls?")}
            >
              Preset: PM Scholarship
            </button>
            <button
              type="button"
              className="pagination-btn"
              onClick={() => setQueryText("How many scholarships are awarded under STSE in Goa each year?")}
            >
              Preset: STSE Goa
            </button>
            <button
              type="button"
              className="pagination-btn"
              onClick={() => setQueryText("गोव्यांत STSE खाला दर वर्षा किती शिष्यवृत्त्यो दितात?")}
            >
              Preset: Konkani STSE
            </button>
          </div>

          <button
            type="submit"
            className="admin-login-submit-btn"
            style={{ width: "auto", padding: "10px 24px", marginTop: 0 }}
            disabled={loading || !queryText.trim()}
          >
            {loading ? "⚙️ Processing Pipeline..." : "⚡ Execute Pipeline Trace"}
          </button>
        </div>
      </form>

      {error && (
        <div className="admin-login-error" style={{ marginBottom: 20 }}>
          {error}
        </div>
      )}

      {/* Debug Trace Output */}
      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Decision Summary */}
          <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
            <div className="kpi-card accent">
              <span className="kpi-label">Routing Decision</span>
              <span className={`badge ${result.route}`} style={{ alignSelf: "flex-start", marginTop: 4 }}>
                {result.route}
              </span>
              <span className="kpi-subtext" style={{ marginTop: 4 }}>Reason: {result.route_reason}</span>
            </div>

            <div className="kpi-card ok">
              <span className="kpi-label">Confidence Score</span>
              <span className="kpi-value">{(result.confidence * 100).toFixed(1)}%</span>
              <span className="kpi-subtext">Threshold: 50.0%</span>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Total Latency</span>
              <span className="kpi-value">{Math.round(result.latencies_ms?.total || 0)} ms</span>
              <span className="kpi-subtext">
                Retr: {Math.round(result.latencies_ms?.retrieve || 0)}ms • Gen: {Math.round(result.latencies_ms?.generate || 0)}ms
              </span>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Translation Backend</span>
              <span className="kpi-value" style={{ fontSize: 16 }}>{result.translator_backend || "None (English)"}</span>
              <span className="kpi-subtext">
                Hints: {result.hints_applied?.length ? result.hints_applied.join(", ") : "None applied"}
              </span>
            </div>
          </div>

          {/* Translated Query & Synthesized Answer */}
          <div className="table-card" style={{ padding: 20 }}>
            <div style={{ marginBottom: 14 }}>
              <span className="kpi-label">Pivoted / Translated Query</span>
              <p style={{ margin: "4px 0", fontSize: 14, fontFamily: "monospace", color: "var(--admin-accent)" }}>
                {result.translated_query}
              </p>
            </div>

            <div>
              <span className="kpi-label">Generated Citizen Answer</span>
              <div
                style={{
                  background: "var(--admin-bg)",
                  border: "1px solid var(--admin-border)",
                  borderRadius: 6,
                  padding: 16,
                  marginTop: 6,
                  fontSize: 13.5,
                  lineHeight: 1.6,
                  color: "var(--admin-text-main)",
                  whiteSpace: "pre-wrap",
                }}
              >
                {result.answer}
              </div>
            </div>
          </div>

          {/* Retrieved Chunks with Hybrid Scores */}
          <div className="table-card">
            <div className="table-controls">
              <span style={{ fontSize: 14, fontWeight: 700 }}>
                Top-k Retrieved Passages with Hybrid Scores ({result.chunks?.length || 0})
              </span>
              <span style={{ fontSize: 12, color: "var(--admin-text-muted)" }}>
                RRF Fusion (60.0 constant) over 384-dim Dense + BM25 Sparse
              </span>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Document / Scheme</th>
                    <th>Dense Sim</th>
                    <th>BM25 Score</th>
                    <th>Fused RRF</th>
                    <th>Passage Snippet</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.chunks || []).map((chunk, idx) => (
                    <tr key={idx}>
                      <td><strong>#{idx + 1}</strong></td>
                      <td style={{ maxWidth: 220 }}>
                        <strong style={{ display: "block" }}>{chunk.title}</strong>
                        <code style={{ fontSize: 11, color: "var(--admin-text-muted)" }}>{chunk.doc_id}</code>
                      </td>
                      <td>{chunk.dense_score != null ? chunk.dense_score.toFixed(4) : "—"}</td>
                      <td>{chunk.bm25_score != null ? chunk.bm25_score.toFixed(2) : "—"}</td>
                      <td>
                        <strong style={{ color: "var(--admin-accent)" }}>
                          {chunk.fused_score != null ? chunk.fused_score.toFixed(4) : "—"}
                        </strong>
                      </td>
                      <td style={{ fontSize: 12, color: "var(--admin-text-muted)", maxWidth: 380, lineHeight: 1.4 }}>
                        {chunk.content}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


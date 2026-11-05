import { useEffect, useState } from "react";

export default function SystemView({ adminKey, onUnauthorized }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rechecking, setRechecking] = useState(false);

  async function loadSystem(isRecheck = false) {
    try {
      if (isRecheck) setRechecking(true);
      else setLoading(true);
      setError("");

      const res = await fetch("/admin/system", {
        headers: { "X-Admin-Key": adminKey },
      });
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (!res.ok) {
        throw new Error(`Failed to load system diagnostics (HTTP ${res.status})`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err.message || "Failed to load system status.");
    } finally {
      setLoading(false);
      setRechecking(false);
    }
  }

  useEffect(() => {
    loadSystem();
  }, [adminKey]);

  return (
    <div className="system-container" role="region" aria-label="System Diagnostics">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>System Diagnostics &amp; Runtime Config</h2>
          <span style={{ fontSize: 12, color: "var(--admin-text-muted)" }}>
            Read-only configuration parameters &amp; service health checks (secrets scrubbed)
          </span>
        </div>
        <button
          type="button"
          className="pagination-btn"
          onClick={() => loadSystem(true)}
          disabled={rechecking || loading}
        >
          {rechecking ? "Checking..." : "🔄 Recheck Health"}
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
          <div className="empty-state-title">Diagnostics Error</div>
          <div className="empty-state-sub">{error}</div>
          <button type="button" className="retry-btn" onClick={() => loadSystem()}>
            Retry
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Live Service Health */}
          <div className="table-card" style={{ padding: 20 }}>
            <span className="kpi-label" style={{ display: "block", marginBottom: 16 }}>
              Live Service Connectivity
            </span>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14 }}>
              {(data?.health || []).map((h) => (
                <div
                  key={h.name}
                  style={{
                    background: "var(--admin-bg)",
                    border: "1px solid var(--admin-border)",
                    borderRadius: 8,
                    padding: 16,
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                  }}
                >
                  <div className={`health-dot ${h.ok ? "ok" : "err"}`} style={{ width: 12, height: 12 }} />
                  <div>
                    <strong style={{ display: "block", fontSize: 14, textTransform: "capitalize" }}>
                      {h.name} Service
                    </strong>
                    <span style={{ fontSize: 12, color: h.ok ? "var(--admin-ok)" : "var(--admin-err)" }}>
                      {h.ok ? `Operational (${h.detail})` : `Failed (${h.detail})`}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Model Roster */}
          <div className="table-card" style={{ padding: 20 }}>
            <span className="kpi-label" style={{ display: "block", marginBottom: 14 }}>
              Configured Machine Learning Models
            </span>
            <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 13 }}>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--admin-border)", paddingBottom: 8 }}>
                <span style={{ color: "var(--admin-text-muted)" }}>Dense Embedding Model:</span>
                <code>{data?.models?.embedding || "all-MiniLM-L6-v2"} (384-dim)</code>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--admin-border)", paddingBottom: 8 }}>
                <span style={{ color: "var(--admin-text-muted)" }}>LLM Generator (Ollama):</span>
                <code>{data?.models?.generator || "llama3.2"}</code>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--admin-border)", paddingBottom: 8 }}>
                <span style={{ color: "var(--admin-text-muted)" }}>Ollama Service URL:</span>
                <code>{data?.models?.ollama_url || "http://localhost:11434"}</code>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: 4 }}>
                <span style={{ color: "var(--admin-text-muted)" }}>Translation Engine:</span>
                <strong>{data?.translator_backend || "not_loaded"}</strong>
              </div>
            </div>
          </div>

          {/* Operational Tuning Knobs */}
          <div className="table-card" style={{ padding: 20 }}>
            <span className="kpi-label" style={{ display: "block", marginBottom: 14 }}>
              Calibrated RAG Parameters
            </span>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
              <div className="kpi-card">
                <span className="kpi-label">Confidence Threshold</span>
                <span className="kpi-value" style={{ fontSize: 20 }}>
                  {data?.thresholds?.confidence_threshold ?? 0.50}
                </span>
                <span className="kpi-subtext">Direct vs Refusal cutoff</span>
              </div>
              <div className="kpi-card">
                <span className="kpi-label">Top-k Passages</span>
                <span className="kpi-value" style={{ fontSize: 20 }}>
                  {data?.thresholds?.top_k ?? 5}
                </span>
                <span className="kpi-subtext">RRF merged chunk limit</span>
              </div>
              <div className="kpi-card">
                <span className="kpi-label">Chunk Size</span>
                <span className="kpi-value" style={{ fontSize: 20 }}>
                  {data?.thresholds?.chunk_size_words ?? 300} words
                </span>
                <span className="kpi-subtext">Word window per passage</span>
              </div>
              <div className="kpi-card">
                <span className="kpi-label">Handmade Hints</span>
                <span className="kpi-value" style={{ fontSize: 20 }}>
                  {String(data?.thresholds?.use_retrieval_hints ?? false)}
                </span>
                <span className="kpi-subtext">USE_RETRIEVAL_HINTS flag</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


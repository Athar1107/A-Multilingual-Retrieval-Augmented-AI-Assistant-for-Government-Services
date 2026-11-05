import { useEffect, useState } from "react";

export default function QueriesView({ adminKey, onUnauthorized }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters
  const [limit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [routeFilter, setRouteFilter] = useState("");
  const [langFilter, setLangFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Selected query for detail drawer
  const [selectedQuery, setSelectedQuery] = useState(null);

  async function fetchQueries() {
    try {
      setLoading(true);
      setError("");
      const params = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
      });
      if (routeFilter) params.append("route", routeFilter);
      if (langFilter) params.append("language", langFilter);
      if (statusFilter) params.append("status", statusFilter);
      if (searchQuery.trim()) params.append("q", searchQuery.trim());

      const res = await fetch(`/admin/queries?${params.toString()}`, {
        headers: { "X-Admin-Key": adminKey },
      });
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (!res.ok) {
        throw new Error(`Failed to load query log (HTTP ${res.status})`);
      }
      const data = await res.json();
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message || "Failed to load queries.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchQueries();
  }, [adminKey, offset, routeFilter, langFilter, statusFilter]);

  function handleSearchSubmit(e) {
    e.preventDefault();
    setOffset(0);
    fetchQueries();
  }

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="queries-container" role="region" aria-label="Query Audit Log">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>Query Audit Ledger</h2>
        <span style={{ fontSize: 12, color: "var(--admin-text-muted)" }}>
          Persisted live query records (retained for 30 days, PII sanitized)
        </span>
      </div>

      <div className="table-card">
        {/* Filter Toolbar */}
        <form className="table-controls" onSubmit={handleSearchSubmit}>
          <div className="search-input-group">
            <span aria-hidden="true">🔍</span>
            <input
              type="text"
              placeholder="Search query preview..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search query preview"
            />
          </div>

          <div className="filter-group">
            <select
              className="admin-select"
              value={routeFilter}
              onChange={(e) => {
                setRouteFilter(e.target.value);
                setOffset(0);
              }}
              aria-label="Filter by Route"
            >
              <option value="">All Routes</option>
              <option value="direct">Direct Match</option>
              <option value="fallback_recovered">Fallback Recovered</option>
              <option value="fallback_failed">Fallback Refusal</option>
            </select>

            <select
              className="admin-select"
              value={langFilter}
              onChange={(e) => {
                setLangFilter(e.target.value);
                setOffset(0);
              }}
              aria-label="Filter by Language"
            >
              <option value="">All Languages</option>
              <option value="en">English (EN)</option>
              <option value="kok">Goan Konkani (KOK)</option>
            </select>

            <select
              className="admin-select"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setOffset(0);
              }}
              aria-label="Filter by Status"
            >
              <option value="">All Statuses</option>
              <option value="ok">Success (ok)</option>
              <option value="error">Error</option>
            </select>

            <button type="submit" className="pagination-btn">
              Apply
            </button>
          </div>
        </form>

        {/* Table */}
        {loading && items.length === 0 ? (
          <div style={{ padding: 24 }}>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton-line" style={{ height: 32 }} />
            ))}
          </div>
        ) : error ? (
          <div className="empty-state">
            <div className="empty-state-icon">⚠️</div>
            <div className="empty-state-title">Error Loading Queries</div>
            <div className="empty-state-sub">{error}</div>
            <button type="button" className="retry-btn" onClick={fetchQueries}>
              Retry
            </button>
          </div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📄</div>
            <div className="empty-state-title">No Queries Found</div>
            <div className="empty-state-sub">No query logs match the current filters.</div>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Lang</th>
                  <th>Query Preview</th>
                  <th>Route</th>
                  <th>Confidence</th>
                  <th>Latency</th>
                  <th>Docs</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr
                    key={row.id}
                    className="clickable"
                    onClick={() => setSelectedQuery(row)}
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setSelectedQuery(row);
                      }
                    }}
                    role="button"
                    aria-label={`View details for query: ${row.query_preview}`}
                  >
                    <td style={{ whiteSpace: "nowrap", color: "var(--admin-text-muted)" }}>
                      {new Date(row.ts * 1000).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </td>
                    <td>
                      <span className="badge" style={{ background: "#1e293b" }}>
                        {row.language?.toUpperCase() || "N/A"}
                      </span>
                    </td>
                    <td style={{ maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      <strong>{row.query_preview || "—"}</strong>
                    </td>
                    <td>
                      <span className={`badge ${row.route || "unknown"}`}>
                        {row.route?.replace("_", " ") || "unknown"}
                      </span>
                    </td>
                    <td>{row.confidence != null ? `${(row.confidence * 100).toFixed(1)}%` : "—"}</td>
                    <td>{row.latency_ms ? `${Math.round(row.latency_ms)} ms` : "—"}</td>
                    <td>
                      <span style={{ fontSize: 11, color: "var(--admin-text-muted)" }}>
                        {row.retrieved_doc_ids?.length || 0}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${row.status === "ok" ? "ok" : "err"}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="pagination-bar">
          <span style={{ fontSize: 12, color: "var(--admin-text-muted)" }}>
            Showing {items.length ? offset + 1 : 0} - {Math.min(offset + limit, total)} of {total} queries
          </span>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button
              type="button"
              className="pagination-btn"
              disabled={offset === 0 || loading}
              onClick={() => setOffset(Math.max(0, offset - limit))}
            >
              Previous
            </button>
            <span style={{ fontSize: 12, fontWeight: 600 }}>
              {currentPage} / {totalPages}
            </span>
            <button
              type="button"
              className="pagination-btn"
              disabled={offset + limit >= total || loading}
              onClick={() => setOffset(offset + limit)}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Slide-over Detail Drawer */}
      {selectedQuery && (
        <div className="drawer-backdrop" onClick={() => setSelectedQuery(null)}>
          <div
            className="drawer-panel"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="drawer-title"
          >
            <div className="drawer-header">
              <span id="drawer-title" className="drawer-title">
                Query Audit Detail
              </span>
              <button
                type="button"
                className="drawer-close"
                onClick={() => setSelectedQuery(null)}
                aria-label="Close drawer"
              >
                ✕
              </button>
            </div>

            <div className="drawer-body">
              <div style={{ marginBottom: 20 }}>
                <span className="kpi-label">Sanitized Query Preview</span>
                <p style={{ fontSize: 15, fontWeight: 700, margin: "6px 0 0", color: "var(--admin-text-main)" }}>
                  {selectedQuery.query_preview}
                </p>
              </div>

              <div className="kpi-grid" style={{ gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
                <div className="kpi-card">
                  <span className="kpi-label">Routing Decision</span>
                  <span className={`badge ${selectedQuery.route || "unknown"}`} style={{ alignSelf: "flex-start", marginTop: 4 }}>
                    {selectedQuery.route?.replace("_", " ") || "unknown"}
                  </span>
                </div>
                <div className="kpi-card">
                  <span className="kpi-label">Confidence Score</span>
                  <span style={{ fontSize: 18, fontWeight: 800 }}>
                    {selectedQuery.confidence != null ? `${(selectedQuery.confidence * 100).toFixed(1)}%` : "N/A"}
                  </span>
                </div>
              </div>

              {/* Stage Latencies */}
              <div style={{ background: "var(--admin-bg)", border: "1px solid var(--admin-border)", borderRadius: 8, padding: 16, marginBottom: 20 }}>
                <span className="kpi-label" style={{ display: "block", marginBottom: 12 }}>
                  Latency Breakdown (Total: {Math.round(selectedQuery.latency_ms || 0)} ms)
                </span>
                <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--admin-text-muted)" }}>1. Inbound Translation:</span>
                    <span>{selectedQuery.latency_translate_in_ms ? `${Math.round(selectedQuery.latency_translate_in_ms)} ms` : "0 ms"}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--admin-text-muted)" }}>2. Hybrid Dense + BM25 Retrieval:</span>
                    <span>{selectedQuery.latency_retrieve_ms ? `${Math.round(selectedQuery.latency_retrieve_ms)} ms` : "0 ms"}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--admin-text-muted)" }}>3. LLM Synthesis (Ollama):</span>
                    <span>{selectedQuery.latency_generate_ms ? `${Math.round(selectedQuery.latency_generate_ms)} ms` : "0 ms"}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--admin-text-muted)" }}>4. Outbound Translation:</span>
                    <span>{selectedQuery.latency_translate_out_ms ? `${Math.round(selectedQuery.latency_translate_out_ms)} ms` : "0 ms"}</span>
                  </div>
                </div>
              </div>

              {/* Retrieved Doc IDs */}
              <div style={{ marginBottom: 20 }}>
                <span className="kpi-label">Retrieved Official Schemes ({selectedQuery.retrieved_doc_ids?.length || 0})</span>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                  {(selectedQuery.retrieved_doc_ids || []).map((docId) => (
                    <span
                      key={docId}
                      style={{
                        background: "var(--admin-surface-alt)",
                        border: "1px solid var(--admin-border)",
                        padding: "4px 8px",
                        borderRadius: 4,
                        fontSize: 12,
                        fontFamily: "monospace",
                      }}
                    >
                      {docId}
                    </span>
                  ))}
                  {!selectedQuery.retrieved_doc_ids?.length && (
                    <span style={{ color: "var(--admin-text-muted)", fontSize: 13 }}>
                      None retrieved (refusal or direct fallback)
                    </span>
                  )}
                </div>
              </div>

              {/* Metadata */}
              <div style={{ fontSize: 12, color: "var(--admin-text-muted)", borderTop: "1px solid var(--admin-border)", paddingTop: 14 }}>
                <p style={{ margin: "4px 0" }}>Query ID: <code>{selectedQuery.id}</code></p>
                <p style={{ margin: "4px 0" }}>Translator Engine: <strong>{selectedQuery.translator_backend || "None (English native)"}</strong></p>
                <p style={{ margin: "4px 0" }}>Source Channel: <strong>{selectedQuery.source || "citizen"}</strong></p>
                {selectedQuery.error_type && (
                  <p style={{ margin: "4px 0", color: "var(--admin-err)" }}>
                    Error Type: <strong>{selectedQuery.error_type}</strong>
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


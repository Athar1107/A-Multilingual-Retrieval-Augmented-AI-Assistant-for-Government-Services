import { useEffect, useState } from "react";

export default function CorpusView({ adminKey, onUnauthorized }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchDoc, setSearchDoc] = useState("");

  // Inspect document chunks
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [docDetail, setDocDetail] = useState(null);
  const [loadingDocDetail, setLoadingDocDetail] = useState(false);

  // Re-index state & modal
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [reindexStatus, setReindexStatus] = useState(null);
  const [reindexing, setReindexing] = useState(false);
  const [reindexMessage, setReindexMessage] = useState("");

  async function loadCorpus() {
    try {
      setLoading(true);
      setError("");
      const res = await fetch("/admin/corpus", {
        headers: { "X-Admin-Key": adminKey },
      });
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (!res.ok) {
        throw new Error(`Failed to load corpus status (HTTP ${res.status})`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err.message || "Failed to load corpus data.");
    } finally {
      setLoading(false);
    }
  }

  async function checkReindexStatus() {
    try {
      const res = await fetch("/admin/reindex/status", {
        headers: { "X-Admin-Key": adminKey },
      });
      if (res.ok) {
        const status = await res.json();
        setReindexStatus(status);
        if (status.running) {
          setReindexing(true);
        } else if (reindexing) {
          setReindexing(false);
          loadCorpus();
        }
      }
    } catch {}
  }

  useEffect(() => {
    loadCorpus();
    checkReindexStatus();
  }, [adminKey]);

  // Polling when reindex is active
  useEffect(() => {
    let timer;
    if (reindexing) {
      timer = setInterval(checkReindexStatus, 2000);
    }
    return () => clearInterval(timer);
  }, [reindexing]);

  async function handleDocInspect(docId) {
    try {
      setSelectedDocId(docId);
      setLoadingDocDetail(true);
      setDocDetail(null);
      const res = await fetch(`/admin/corpus/${encodeURIComponent(docId)}`, {
        headers: { "X-Admin-Key": adminKey },
      });
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (res.ok) {
        const json = await res.json();
        setDocDetail(json);
      }
    } catch {
    } finally {
      setLoadingDocDetail(false);
    }
  }

  async function triggerReindex() {
    setConfirmModalOpen(false);
    setReindexMessage("");
    try {
      const res = await fetch("/admin/reindex", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Key": adminKey,
        },
        body: JSON.stringify({ confirm: true }),
      });
      if (res.status === 401) {
        onUnauthorized();
        return;
      }
      if (res.status === 409) {
        setReindexMessage("⚠️ Re-index is already running in background.");
        setReindexing(true);
        return;
      }
      if (!res.ok) {
        throw new Error("Failed to launch reindex background job.");
      }
      setReindexing(true);
      setReindexMessage("✓ Corpus reindex initiated in background. Polling status...");
      checkReindexStatus();
    } catch (err) {
      setReindexMessage(`Error: ${err.message}`);
    }
  }

  const documents = (data?.documents || []).filter((doc) => {
    if (!searchDoc.trim()) return true;
    const term = searchDoc.toLowerCase();
    return (
      doc.title.toLowerCase().includes(term) ||
      doc.doc_id.toLowerCase().includes(term) ||
      doc.source.toLowerCase().includes(term)
    );
  });

  return (
    <div className="corpus-container" role="region" aria-label="Corpus Management">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>Verified Corpus Management</h2>
          <span style={{ fontSize: 12, color: "var(--admin-text-muted)" }}>
            Real-time ChromaDB collection index &amp; source document mappings
          </span>
        </div>
        <button
          type="button"
          className="admin-login-submit-btn"
          style={{ width: "auto", padding: "8px 16px", marginTop: 0 }}
          onClick={() => setConfirmModalOpen(true)}
          disabled={reindexing}
        >
          {reindexing ? "⏳ Reindexing in progress..." : "⚙️ Re-index Corpus"}
        </button>
      </div>

      {reindexMessage && (
        <div
          style={{
            padding: "10px 16px",
            background: "rgba(6, 182, 212, 0.15)",
            border: "1px solid var(--admin-accent)",
            color: "var(--admin-text-main)",
            borderRadius: 8,
            marginBottom: 20,
            fontSize: 13,
          }}
        >
          {reindexMessage}
        </div>
      )}

      {/* Source Breakdown Cards */}
      <div className="kpi-grid">
        {(data?.sources || []).map((s) => (
          <div key={s.source} className="kpi-card accent">
            <span className="kpi-label">Source: {s.source}</span>
            <span className="kpi-value">{s.chunks}</span>
            <span className="kpi-subtext">{s.documents} verified schemes</span>
          </div>
        ))}
        <div className="kpi-card ok">
          <span className="kpi-label">Total Corpus Chunks</span>
          <span className="kpi-value">{data?.total_chunks || 0}</span>
          <span className="kpi-subtext">{data?.total_documents || 0} indexed documents</span>
        </div>
      </div>

      {/* Documents Table */}
      <div className="table-card">
        <div className="table-controls">
          <div className="search-input-group" style={{ width: 340 }}>
            <span aria-hidden="true">🔍</span>
            <input
              type="text"
              placeholder="Filter by title, ID or source portal..."
              value={searchDoc}
              onChange={(e) => setSearchDoc(e.target.value)}
              aria-label="Filter documents"
            />
          </div>
          <span style={{ fontSize: 12, color: "var(--admin-text-muted)" }}>
            Showing {documents.length} of {data?.total_documents || 0} verified schemes
          </span>
        </div>

        {loading ? (
          <div style={{ padding: 24 }}>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton-line" style={{ height: 28 }} />
            ))}
          </div>
        ) : error ? (
          <div className="empty-state">
            <div className="empty-state-title">Failed to load corpus</div>
            <div className="empty-state-sub">{error}</div>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Scheme ID</th>
                  <th>Official Title</th>
                  <th>Source Portal</th>
                  <th>Chunks</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.doc_id}>
                    <td>
                      <code style={{ fontSize: 12, color: "var(--admin-accent)" }}>{doc.doc_id}</code>
                    </td>
                    <td>
                      <strong>{doc.title}</strong>
                      {doc.source_url && (
                        <a
                          href={doc.source_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ display: "block", fontSize: 11, color: "var(--admin-text-muted)", marginTop: 2 }}
                        >
                          {doc.source_url} ↗
                        </a>
                      )}
                    </td>
                    <td>
                      <span className="badge" style={{ background: "#1e293b" }}>{doc.source}</span>
                    </td>
                    <td>
                      <strong>{doc.chunk_count}</strong>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="pagination-btn"
                        onClick={() => handleDocInspect(doc.doc_id)}
                      >
                        Inspect Chunks
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Re-index Confirmation Modal */}
      {confirmModalOpen && (
        <div className="drawer-backdrop" onClick={() => setConfirmModalOpen(false)}>
          <div
            className="admin-login-card"
            style={{ maxWidth: 460 }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="admin-login-header">
              <h1 style={{ color: "var(--admin-warn)" }}>⚠️ Confirm Full Corpus Reindex</h1>
              <p>
                This will re-parse active government registers, generate 384-dim dense embeddings, and rebuild
                the BM25 sparse index in background.
              </p>
            </div>
            <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
              <button
                type="button"
                className="admin-login-submit-btn"
                style={{ background: "var(--admin-surface-alt)", color: "var(--admin-text-main)" }}
                onClick={() => setConfirmModalOpen(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="admin-login-submit-btn"
                style={{ background: "var(--admin-accent)" }}
                onClick={triggerReindex}
              >
                Proceed with Reindex
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chunk Inspector Drawer */}
      {selectedDocId && (
        <div className="drawer-backdrop" onClick={() => setSelectedDocId(null)}>
          <div
            className="drawer-panel"
            style={{ width: 680 }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="drawer-header">
              <div>
                <span className="drawer-title">Document Chunks</span>
                <span style={{ display: "block", fontSize: 12, color: "var(--admin-accent)", marginTop: 2 }}>
                  {selectedDocId}
                </span>
              </div>
              <button type="button" className="drawer-close" onClick={() => setSelectedDocId(null)}>
                ✕
              </button>
            </div>

            <div className="drawer-body">
              {loadingDocDetail ? (
                <div>
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="skeleton-line" style={{ height: 60, marginBottom: 12 }} />
                  ))}
                </div>
              ) : !docDetail || !docDetail.chunks?.length ? (
                <div className="empty-state">
                  <div className="empty-state-title">No Chunks Found</div>
                  <div className="empty-state-sub">Document may not have active chunks in ChromaDB.</div>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  <p style={{ margin: "0 0 10px", fontSize: 13, color: "var(--admin-text-muted)" }}>
                    Total {docDetail.chunks.length} chunks indexed with sliding word windows.
                  </p>
                  {docDetail.chunks.map((chk, idx) => (
                    <div
                      key={chk.chunk_id || idx}
                      style={{
                        background: "var(--admin-bg)",
                        border: "1px solid var(--admin-border)",
                        borderRadius: 8,
                        padding: 16,
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: "var(--admin-accent)" }}>
                          Chunk #{chk.chunk_index != null ? chk.chunk_index : idx} (ID: {chk.chunk_id})
                        </span>
                        <span style={{ fontSize: 11, color: "var(--admin-text-muted)" }}>
                          {chk.text ? `${chk.text.split(" ").length} words` : "0 words"}
                        </span>
                      </div>
                      <p style={{ margin: 0, fontSize: 12.5, lineHeight: 1.6, color: "var(--admin-text-main)", whiteSpace: "pre-wrap" }}>
                        {chk.text}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


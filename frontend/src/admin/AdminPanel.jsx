import { useEffect, useState } from "react";
import "./admin.css";

import OverviewView from "./OverviewView";
import QueriesView from "./QueriesView";
import CorpusView from "./CorpusView";
import EvalView from "./EvalView";
import TestConsoleView from "./TestConsoleView";
import SystemView from "./SystemView";

export default function AdminPanel({ onNavigateHome }) {
  // CRITICAL: Key held in React state ONLY (NEVER in localStorage/sessionStorage)
  const [adminKey, setAdminKey] = useState("");
  const [adminUser, setAdminUser] = useState("Atharv");
  const [activeTab, setActiveTab] = useState("overview");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Login form states
  const [loginMode, setLoginMode] = useState("credentials"); // "credentials" or "key"
  const [usernameInput, setUsernameInput] = useState("Atharv");
  const [passwordInput, setPasswordInput] = useState("admin@1234");
  const [keyInput, setKeyInput] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);

  // Topbar health indicators
  const [systemHealth, setSystemHealth] = useState({
    ollama: false,
    chroma: false,
    translator: false,
  });

  async function handleLogin(e) {
    e?.preventDefault();
    setLoginError("");
    setLoggingIn(true);

    try {
      const payload =
        loginMode === "key"
          ? { admin_key: keyInput.trim() }
          : { username: usernameInput.trim(), password: passwordInput };

      const res = await fetch("/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.status === 503) {
        throw new Error("Admin API is not configured on the backend server.");
      }
      if (!res.ok) {
        throw new Error("Invalid administrator credentials or API key.");
      }

      const data = await res.json();
      setAdminKey(data.admin_key);
      setAdminUser(data.username || "Atharv");
      fetchQuickHealth(data.admin_key);
    } catch (err) {
      setLoginError(err.message || "Failed to authenticate.");
    } finally {
      setLoggingIn(false);
    }
  }

  async function fetchQuickHealth(keyToUse) {
    const k = keyToUse || adminKey;
    if (!k) return;
    try {
      const res = await fetch("/admin/system", {
        headers: { "X-Admin-Key": k },
      });
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      if (res.ok) {
        const data = await res.json();
        const healthMap = {};
        for (const h of data.health || []) {
          healthMap[h.name] = h.ok;
        }
        setSystemHealth({
          ollama: Boolean(healthMap.ollama),
          chroma: Boolean(healthMap.chroma),
          translator: Boolean(healthMap.translator),
        });
      }
    } catch {}
  }

  function handleUnauthorized() {
    // Fail safe: flush in-memory key on any 401
    setAdminKey("");
    setLoginError("Session expired or authentication failed. Please sign in again.");
  }

  function handleLogout() {
    setAdminKey("");
    setPasswordInput("");
    setKeyInput("");
  }

  // Not logged in -> Render Login Card
  if (!adminKey) {
    return (
      <div className="admin-login-overlay">
        <div className="admin-login-card" role="dialog" aria-labelledby="login-title">
          <div className="admin-login-header">
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 10,
                background: "linear-gradient(135deg, #0891b2, #06b6d4)",
                color: "#fff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 12px",
                fontSize: 22,
              }}
            >
              🛡️
            </div>
            <h1 id="login-title">Seva AI Admin Command Center</h1>
            <p>Secure operational governance, corpus telemetry, and audit suite</p>
          </div>

          <div style={{ display: "flex", gap: 8, marginBottom: 18 }}>
            <button
              type="button"
              className={`pagination-btn ${loginMode === "credentials" ? "active" : ""}`}
              style={{
                flex: 1,
                background: loginMode === "credentials" ? "var(--admin-accent)" : "var(--admin-surface-alt)",
                color: loginMode === "credentials" ? "#fff" : "var(--admin-text-main)",
                fontWeight: 600,
              }}
              onClick={() => setLoginMode("credentials")}
            >
              Credentials (Atharv)
            </button>
            <button
              type="button"
              className={`pagination-btn ${loginMode === "key" ? "active" : ""}`}
              style={{
                flex: 1,
                background: loginMode === "key" ? "var(--admin-accent)" : "var(--admin-surface-alt)",
                color: loginMode === "key" ? "#fff" : "var(--admin-text-main)",
                fontWeight: 600,
              }}
              onClick={() => setLoginMode("key")}
            >
              API Key (X-Admin-Key)
            </button>
          </div>

          <form onSubmit={handleLogin}>
            {loginMode === "credentials" ? (
              <>
                <div className="admin-form-group">
                  <label htmlFor="adminUser">Administrator Username</label>
                  <input
                    id="adminUser"
                    type="text"
                    value={usernameInput}
                    onChange={(e) => setUsernameInput(e.target.value)}
                    required
                    autoFocus
                  />
                </div>
                <div className="admin-form-group">
                  <label htmlFor="adminPass">Administrator Password</label>
                  <input
                    id="adminPass"
                    type="password"
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    required
                  />
                </div>
              </>
            ) : (
              <div className="admin-form-group">
                <label htmlFor="adminKey">X-Admin-Key Header Value</label>
                <input
                  id="adminKey"
                  type="password"
                  placeholder="Enter ADMIN_API_KEY from environment"
                  value={keyInput}
                  onChange={(e) => setKeyInput(e.target.value)}
                  required
                  autoFocus
                />
              </div>
            )}

            <button
              type="submit"
              className="admin-login-submit-btn"
              disabled={loggingIn}
            >
              {loggingIn ? "Verifying..." : "Sign In to Admin Center"}
            </button>

            {loginError && <div className="admin-login-error">{loginError}</div>}
          </form>

          {onNavigateHome && (
            <div style={{ marginTop: 20, textAlign: "center" }}>
              <button
                type="button"
                className="admin-return-btn"
                style={{ width: "100%" }}
                onClick={onNavigateHome}
              >
                ← Return to Citizen Assistant
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="admin-root">
      {/* Sidebar Navigation */}
      <aside className={`admin-sidebar ${mobileSidebarOpen ? "open" : ""}`} aria-label="Admin Navigation">
        <div className="admin-sidebar-header">
          <div className="admin-brand">
            <div className="admin-brand-icon">S</div>
            <div className="admin-brand-text">
              <h2>Seva AI</h2>
              <span>Admin Center</span>
            </div>
          </div>
          {mobileSidebarOpen && (
            <button
              type="button"
              className="drawer-close"
              onClick={() => setMobileSidebarOpen(false)}
              aria-label="Close menu"
            >
              ✕
            </button>
          )}
        </div>

        <nav className="admin-nav">
          <button
            type="button"
            className={`admin-nav-item ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("overview");
              setMobileSidebarOpen(false);
            }}
          >
            <span className="admin-nav-icon">📊</span>
            <span>Overview &amp; KPIs</span>
          </button>

          <button
            type="button"
            className={`admin-nav-item ${activeTab === "queries" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("queries");
              setMobileSidebarOpen(false);
            }}
          >
            <span className="admin-nav-icon">🔍</span>
            <span>Query Audit Log</span>
          </button>

          <button
            type="button"
            className={`admin-nav-item ${activeTab === "corpus" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("corpus");
              setMobileSidebarOpen(false);
            }}
          >
            <span className="admin-nav-icon">📚</span>
            <span>Corpus &amp; Reindex</span>
          </button>

          <button
            type="button"
            className={`admin-nav-item ${activeTab === "eval" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("eval");
              setMobileSidebarOpen(false);
            }}
          >
            <span className="admin-nav-icon">🎯</span>
            <span>Evaluation Benchmarks</span>
          </button>

          <button
            type="button"
            className={`admin-nav-item ${activeTab === "test" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("test");
              setMobileSidebarOpen(false);
            }}
          >
            <span className="admin-nav-icon">⚡</span>
            <span>RAG Test Console</span>
          </button>

          <button
            type="button"
            className={`admin-nav-item ${activeTab === "system" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("system");
              setMobileSidebarOpen(false);
            }}
          >
            <span className="admin-nav-icon">🛠️</span>
            <span>System Diagnostics</span>
          </button>
        </nav>

        <div className="admin-sidebar-footer">
          {onNavigateHome && (
            <button type="button" className="admin-return-btn" onClick={onNavigateHome}>
              ← Return to Chat
            </button>
          )}
        </div>
      </aside>

      {/* Main Layout Area */}
      <div className="admin-main">
        <header className="admin-topbar">
          <div className="admin-topbar-left">
            <button
              type="button"
              className="admin-menu-toggle"
              onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
              aria-label="Toggle Navigation Menu"
            >
              ☰
            </button>
            <span className="admin-topbar-title">
              {activeTab === "overview" && "System Overview"}
              {activeTab === "queries" && "Query Audit Ledger"}
              {activeTab === "corpus" && "Corpus & Index Management"}
              {activeTab === "eval" && "Evaluation & Accuracy Runs"}
              {activeTab === "test" && "RAG Pipeline Test Console"}
              {activeTab === "system" && "System & Model Diagnostics"}
            </span>
          </div>

          <div className="admin-topbar-right">
            {/* Live Health Dots */}
            <div className="admin-health-pills" title="Live Service Health">
              <div className="health-pill">
                <span className={`health-dot ${systemHealth.ollama ? "ok" : "err"}`} />
                <span>Ollama</span>
              </div>
              <div className="health-pill">
                <span className={`health-dot ${systemHealth.chroma ? "ok" : "err"}`} />
                <span>Chroma</span>
              </div>
              <div className="health-pill">
                <span className={`health-dot ${systemHealth.translator ? "ok" : "err"}`} />
                <span>Translator</span>
              </div>
            </div>

            <div className="admin-user-tag">
              <span>👤</span>
              <strong>{adminUser}</strong>
            </div>

            <button
              type="button"
              className="admin-logout-btn"
              onClick={handleLogout}
              aria-label="Sign out from admin center"
            >
              Sign Out
            </button>
          </div>
        </header>

        {/* Tab Content Body */}
        <main className="admin-body">
          {activeTab === "overview" && (
            <OverviewView adminKey={adminKey} onUnauthorized={handleUnauthorized} />
          )}
          {activeTab === "queries" && (
            <QueriesView adminKey={adminKey} onUnauthorized={handleUnauthorized} />
          )}
          {activeTab === "corpus" && (
            <CorpusView adminKey={adminKey} onUnauthorized={handleUnauthorized} />
          )}
          {activeTab === "eval" && (
            <EvalView adminKey={adminKey} onUnauthorized={handleUnauthorized} />
          )}
          {activeTab === "test" && (
            <TestConsoleView adminKey={adminKey} onUnauthorized={handleUnauthorized} />
          )}
          {activeTab === "system" && (
            <SystemView adminKey={adminKey} onUnauthorized={handleUnauthorized} />
          )}
        </main>
      </div>
    </div>
  );
}


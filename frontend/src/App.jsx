import { useEffect, useRef, useState, useCallback, lazy, Suspense } from "react";

const AdminPanel = lazy(() => import("./admin/AdminPanel"));

const MAX_CHARS = 2000;

const SUGGESTIONS_BY_LANG = {
  en: [
    {
      category: "Scholarships",
      icon: "🎓",
      title: "PM Scholarship Benefits",
      question: "What is the PM scholarship benefit amount and eligibility?",
    },
    {
      category: "Goa Schemes",
      icon: "🏛️",
      title: "Goa Welfare Schemes",
      question: "Which schemes are available for residents and students in Goa?",
    },
    {
      category: "Social Security",
      icon: "🛡️",
      title: "Dayanand Social Security",
      question: "How do I apply for the Dayanand Social Security Scheme?",
    },
    {
      category: "How to Apply",
      icon: "📋",
      title: "Online Application Guide",
      question: "How do I apply for a government scheme online step by step?",
    },
  ],
  kok: [
    {
      category: "शिष्यवृत्ती",
      icon: "🎓",
      title: "प्रधानमंत्री शिष्यवृत्ती",
      question: "प्रधानमंत्री शिष्यवृत्ती येवजणेचे फायदे कितें आसात?",
    },
    {
      category: "गोंय येवजण्यो",
      icon: "🏛️",
      title: "विद्यार्थी शिष्यवृत्ती",
      question: "विद्यार्थ्यांखातीर खंयच्यो शिष्यवृत्ती उपलब्ध आसात?",
    },
    {
      category: "समाज कल्याण",
      icon: "🛡️",
      title: "गृह आधार योजना",
      question: "गृह आधार योजनेची माहिती दिवची",
    },
    {
      category: "अर्ज प्रक्रिया",
      icon: "📋",
      title: "अर्ज कसा करावा",
      question: "सरकारी योजनेखातीर अर्ज कसो करचो?",
    },
  ],
};

const CATEGORIES = [
  {
    name: "Scholarships & Education",
    kokName: "शिक्षण आनी शिष्यवृत्ती",
    icon: "🎓",
    query: "Which scholarships are available for students?",
  },
  {
    name: "Goa State Schemes",
    kokName: "गोंय राज्य येवजण्यो",
    icon: "🏛️",
    query: "What schemes are offered by the Goa government?",
  },
  {
    name: "Welfare & Pensions",
    kokName: "कल्याण आनी निवृत्तीवेतन",
    icon: "🤝",
    query: "What are the welfare and pension schemes available?",
  },
  {
    name: "Application Process",
    kokName: "अर्ज प्रक्रिया",
    icon: "📑",
    query: "How do I apply for a government scheme?",
  },
];

// Preserved exact security operation: only permits http: and https: protocols
function safeSourceUrl(value) {
  try {
    const url = new URL(String(value));
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function extractHostname(urlStr) {
  try {
    const hostname = new URL(urlStr).hostname.replace(/^www\./, "");
    return hostname;
  } catch {
    return "Official Portal";
  }
}

// 100% safe text formatting (zero innerHTML, strictly safe React text nodes)
function FormattedMessageText({ text }) {
  if (!text) return null;

  const paragraphs = text.split(/\n\s*\n/);

  return (
    <div className="formatted-text">
      {paragraphs.map((para, pIdx) => {
        const lines = para.split("\n");
        const trimmedLines = lines.map((l) => l.trim()).filter(Boolean);

        const isBulletList =
          trimmedLines.length > 0 &&
          trimmedLines.every((l) => l.startsWith("- ") || l.startsWith("* ") || l.startsWith("• "));

        const isNumberedList =
          trimmedLines.length > 0 &&
          trimmedLines.every((l) => /^\d+[\.\)]\s/.test(l));

        if (isBulletList) {
          return (
            <ul key={pIdx} className="message-list bullet">
              {trimmedLines.map((line, lIdx) => (
                <li key={lIdx}>
                  {formatInline(line.replace(/^[-*•]\s+/, ""))}
                </li>
              ))}
            </ul>
          );
        }

        if (isNumberedList) {
          return (
            <ol key={pIdx} className="message-list numbered">
              {trimmedLines.map((line, lIdx) => (
                <li key={lIdx}>
                  {formatInline(line.replace(/^\d+[\.\)]\s+/, ""))}
                </li>
              ))}
            </ol>
          );
        }

        return (
          <p key={pIdx} className="message-paragraph">
            {lines.map((line, lIdx) => (
              <span key={lIdx}>
                {lIdx > 0 && <br />}
                {formatInline(line)}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}

function formatInline(str) {
  // Safe inline bold parser without dangerouslySetInnerHTML
  const parts = str.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      return <strong key={idx}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function Message({ message }) {
  const isUser = message.role === "user";
  const isTyping = message.role === "typing";
  const isError = message.role === "error";
  const [copied, setCopied] = useState(false);

  const safeSources = (message.sources || [])
    .map((source) => ({
      title: String(source.title || "Official source"),
      url: safeSourceUrl(source.source_url),
    }))
    .filter((source) => source.url);

  function handleCopy() {
    if (!message.text) return;
    navigator.clipboard.writeText(message.text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <article
      className={`message ${isUser ? "user" : "assistant"} ${isTyping ? "typing" : ""} ${isError ? "error" : ""}`}
    >
      <div className="avatar" aria-hidden="true">
        {isUser ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
            <path d="m9 12 2 2 4-4" />
          </svg>
        )}
      </div>

      <div className="message-content">
        <header className="message-header">
          <span className="author-name">{isUser ? "You" : "Seva Assistant"}</span>
          {!isUser && !isTyping && !isError && (
            <div className="message-actions">
              <button
                type="button"
                className={`action-btn copy-btn ${copied ? "copied" : ""}`}
                onClick={handleCopy}
                title="Copy response to clipboard"
                aria-label="Copy response"
              >
                {copied ? (
                  <>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
          )}
        </header>

        <div className="bubble">
          {isTyping ? (
            <div className="typing-indicator">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-label">{message.text}</span>
            </div>
          ) : (
            <FormattedMessageText text={message.text} />
          )}
        </div>

        {!isUser && !isTyping && !isError && typeof message.confidence === "number" && (
          <footer className="message-footer">
            <div className="message-meta">
              {message.route === "fallback_recovered" ? (
                <span className="grounding-badge recovered">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                    <path d="M3 3v5h5" />
                    <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                    <path d="M16 21h5v-5" />
                  </svg>
                  {Math.round(message.confidence * 100)}% Fallback Recovered
                </span>
              ) : message.route === "fallback_failed" || message.route === "fallback" ? (
                <span className="grounding-badge caution">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  Verify with official portal (Unverified)
                </span>
              ) : (
                <span className="grounding-badge verified">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    <path d="m9 12 2 2 4-4" />
                  </svg>
                  {Math.round(message.confidence * 100)}% Source Grounded
                </span>
              )}
            </div>

            {safeSources.length > 0 && (
              <section className="sources-card" aria-label="Official sources consulted">
                <div className="sources-header">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                  </svg>
                  <span>Official Government Registers</span>
                </div>
                <div className="source-list">
                  {safeSources.map((source) => (
                    <a
                      className="source-chip"
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      key={source.url}
                    >
                      <span className="source-domain">{extractHostname(source.url)}</span>
                      <span className="source-title">{source.title}</span>
                      <svg className="external-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                      </svg>
                    </a>
                  ))}
                </div>
              </section>
            )}
          </footer>
        )}
      </div>
    </article>
  );
}

function Welcome({ onSuggestion, language }) {
  const suggestions = SUGGESTIONS_BY_LANG[language] || SUGGESTIONS_BY_LANG.en;

  return (
    <section className="welcome-hero">
      <div className="hero-emblem-wrap">
        <div className="hero-emblem" aria-hidden="true">
          <svg viewBox="0 0 40 40" fill="none">
            <defs>
              <linearGradient id="emblemGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" />
                <stop offset="50%" stopColor="#6366f1" />
                <stop offset="100%" stopColor="#d97706" />
              </linearGradient>
            </defs>
            <circle cx="20" cy="20" r="18" stroke="url(#emblemGlow)" strokeWidth="1.5" strokeDasharray="3 3" />
            <path d="M20 7 L28 11 L28 21 C28 27.5 23.5 31.5 20 33 C16.5 31.5 12 27.5 12 21 L12 11 Z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
            <circle cx="20" cy="18" r="4" fill="#f59e0b" />
          </svg>
        </div>
        <span className="hero-badge">
          <span className="pulse-dot" />
          GOVERNMENT SERVICES ASSISTANT • बहुभाषिक सहाय्यक
        </span>
      </div>

      <h2 className="hero-heading">
        Clear answers, verified from <span className="gradient-text">official government registers</span>.
      </h2>
      <p className="hero-desc">
        Instant guidance on Indian central schemes, Goa state welfare, scholarships, eligibility criteria, and step-by-step applications.
      </p>

      <div className="trust-pills">
        <span className="trust-pill">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
          Grounded Citations
        </span>
        <span className="trust-pill">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          Zero Data Logging
        </span>
        <span className="trust-pill">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="2" y1="12" x2="22" y2="12" />
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
          </svg>
          English &amp; कोंकणी
        </span>
      </div>

      <div className="suggestion-cards-grid" aria-label="Common citizen queries">
        {suggestions.map((item) => (
          <button
            type="button"
            key={item.question}
            className="suggestion-card"
            onClick={() => onSuggestion(item.question)}
          >
            <div className="card-top">
              <span className="card-icon">{item.icon}</span>
              <span className="card-category">{item.category}</span>
            </div>
            <h3 className="card-title">{item.title}</h3>
            <p className="card-question">{item.question}</p>
            <div className="card-footer">
              <span>Ask this question</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}


// ---------------------------------------------------------------------------
// Auth API helpers
// ---------------------------------------------------------------------------
const API = {
  async post(path, body, token) {
    const headers = { "Content-Type": "application/json" };
    if (token) headers["X-User-Token"] = token;
    const r = await fetch(path, { method: "POST", headers, credentials: "same-origin", body: JSON.stringify(body) });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail || "Request failed");
    return data;
  },
  async get(path, token) {
    const headers = {};
    if (token) headers["X-User-Token"] = token;
    const r = await fetch(path, { headers, credentials: "same-origin" });
    if (!r.ok) return null;
    return r.json().catch(() => null);
  },
  async del(path, token) {
    const headers = {};
    if (token) headers["X-User-Token"] = token;
    const r = await fetch(path, { method: "DELETE", headers, credentials: "same-origin" });
    return r.ok;
  },
};

// ---------------------------------------------------------------------------
// AuthModal – Login / Register / Google Sign-In
// ---------------------------------------------------------------------------
function AuthModal({ onClose, onSuccess }) {
  const [tab, setTab] = useState("login");
  const [form, setForm] = useState({ username: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function field(k) {
    return (e) => setForm((p) => ({ ...p, [k]: e.target.value }));
  }

  async function submit(e) {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      let data;
      if (tab === "login") {
        data = await API.post("/api/auth/login", { username: form.username, password: form.password });
      } else {
        if (!form.full_name.trim()) { setError("Full name is required."); setBusy(false); return; }
        data = await API.post("/api/auth/register", { username: form.username, password: form.password, full_name: form.full_name });
      }
      sessionStorage.setItem("seva_token", data.token);
      onSuccess(data.user, data.token);
    } catch (err) {
      setError(err.message || "Authentication failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function googleSignIn() {
    const email = window.prompt("Enter your Google email address (dev mode):");
    if (!email || !email.includes("@")) return;
    setBusy(true); setError("");
    try {
      const data = await API.post("/api/auth/google", { credential: email, email, name: email.split("@")[0] });
      sessionStorage.setItem("seva_token", data.token);
      onSuccess(data.user, data.token);
    } catch (err) {
      setError(err.message || "Google sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Sign In" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="auth-modal-card">
        <div className="auth-tabs" role="tablist">
          {["login", "register"].map((t) => (
            <button key={t} role="tab" aria-selected={tab === t} className={`auth-tab ${tab === t ? "active" : ""}`} onClick={() => { setTab(t); setError(""); }} type="button">
              {t === "login" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>

        <form className="auth-form" onSubmit={submit} noValidate>
          {tab === "register" && (
            <div className="auth-field">
              <label htmlFor="auth-fullname">Full Name</label>
              <input id="auth-fullname" type="text" value={form.full_name} onChange={field("full_name")} placeholder="Your full name" autoFocus required />
            </div>
          )}
          <div className="auth-field">
            <label htmlFor="auth-username">Username</label>
            <input id="auth-username" type="text" value={form.username} onChange={field("username")} placeholder="Enter username" autoFocus={tab === "login"} required autoComplete="username" />
          </div>
          <div className="auth-field">
            <label htmlFor="auth-password">Password</label>
            <input id="auth-password" type="password" value={form.password} onChange={field("password")} placeholder="Enter password" required autoComplete={tab === "login" ? "current-password" : "new-password"} />
          </div>

          {error && <p className="auth-error-msg" role="alert">{error}</p>}

          <button className="auth-submit-btn" type="submit" disabled={busy}>
            {busy ? "Please wait…" : tab === "login" ? "Sign In" : "Create Account"}
          </button>

          <div className="auth-divider"><span>or</span></div>

          <button type="button" className="google-signin-btn" onClick={googleSignIn} disabled={busy}>
            <svg className="google-icon" width="18" height="18" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          <div className="demo-credentials-box">
            <p className="demo-box-title">Demo credentials</p>
            <button type="button" className="quick-fill-btn" onClick={() => { setTab("login"); setForm({ username: "demo", password: "demo1234", full_name: "" }); }}>
              <code>demo / demo1234</code>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function App() {
  const [currentPath, setCurrentPath] = useState(() => window.location.pathname);
  const [language, setLanguage] = useState("en");
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [serviceUnavailable, setServiceUnavailable] = useState(false);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("seva_theme") || "dark";
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [userToken, setUserToken] = useState(() => sessionStorage.getItem("seva_token") || "");
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [savedConversations, setSavedConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);

  const inputRef = useRef(null);
  const conversationRef = useRef(null);

  useEffect(() => {
    function handlePopState() {
      setCurrentPath(window.location.pathname);
    }
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function navigateTo(path) {
    window.history.pushState(null, "", path);
    setCurrentPath(path);
  }

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("seva_theme", theme);
  }, [theme]);

  useEffect(() => {
    const container = conversationRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, [messages, isLoading]);

  // Restore session on mount
  useEffect(() => {
    const token = sessionStorage.getItem("seva_token");
    if (token) {
      API.get("/api/auth/me", token).then((user) => {
        if (user) { setCurrentUser(user); setUserToken(token); }
        else { sessionStorage.removeItem("seva_token"); setUserToken(""); }
      });
    }
  }, []);

  // Fetch saved conversations when user logs in
  useEffect(() => {
    if (!currentUser || !userToken) { setSavedConversations([]); return; }
    API.get("/api/conversations", userToken).then((list) => {
      if (Array.isArray(list)) setSavedConversations(list);
    });
  }, [currentUser, userToken]);

  function handleAuthSuccess(user, token) {
    setCurrentUser(user);
    setUserToken(token);
    setShowAuthModal(false);
  }

  async function handleSignOut() {
    if (userToken) {
      await API.post("/api/auth/logout", {}, userToken).catch(() => {});
    }
    sessionStorage.removeItem("seva_token");
    setCurrentUser(null);
    setUserToken("");
    setSavedConversations([]);
    setActiveConvId(null);
    setMessages([]);
  }

  async function loadConversation(convId) {
    const data = await API.get("/api/conversations/" + convId, userToken);
    if (!data) return;
    setActiveConvId(convId);
    const rebuilt = [];
    for (const pair of data.messages || []) {
      rebuilt.push({ id: pair.id + "_u", role: "user", text: pair.user_text });
      rebuilt.push({
        id: pair.id + "_a", role: "assistant",
        text: pair.assistant_text,
        confidence: pair.confidence,
        route: pair.route,
        sources: pair.sources || [],
      });
    }
    setMessages(rebuilt);
    if (window.innerWidth <= 768) setSidebarOpen(false);
  }

  async function deleteConversation(convId, e) {
    e.stopPropagation();
    await API.del("/api/conversations/" + convId, userToken);
    setSavedConversations((prev) => prev.filter((c) => c.id !== convId));
    if (activeConvId === convId) { setActiveConvId(null); setMessages([]); }
  }

  function toggleTheme() {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }

  function resizeInput(event) {
    const input = event.currentTarget;
    input.style.height = "auto";
    input.style.height = `${Math.max(48, Math.min(input.scrollHeight, 180))}px`;
  }

  // Preserved exact security operations:
  // 1. Max character limit enforcement (2000 chars)
  // 2. Strict POST /query with same-origin credentials & Content-Type
  // 3. Exact { text, language } body structure expected by backend
  // 4. Rate-limit 429 and server 503 fallback handling
  async function submit(event) {
    event?.preventDefault();
    const text = question.trim();
    if (!text || text.length > MAX_CHARS || isLoading) return;

    setQuestion("");
    if (inputRef.current) inputRef.current.style.height = "48px";
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", text },
    ]);
    setIsLoading(true);

    try {
      const apiKey = import.meta.env.VITE_API_KEY || "";
      const headers = {
        "Content-Type": "application/json",
        Accept: "application/json",
      };
      if (apiKey) headers["X-API-Key"] = apiKey;
      if (userToken) headers["X-User-Token"] = userToken;
      const body = { text, language };
      if (activeConvId) body.conversation_id = activeConvId;
      const response = await fetch("/query", {
        method: "POST",
        headers,
        credentials: "same-origin",
        body: JSON.stringify(body),
      });
      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        const fallback =
          response.status === 429
            ? "Please wait a moment before sending another question."
            : "I’m unable to answer right now. Please try again shortly.";
        setMessages((current) => [
          ...current,
          { id: crypto.randomUUID(), role: "error", text: String(payload.detail || fallback) },
        ]);
        setServiceUnavailable(true);
        return;
      }

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: String(payload.answer || "No answer was generated."),
          confidence: Number(payload.confidence),
          route: payload.route,
          sources: Array.isArray(payload.sources) ? payload.sources : [],
        },
      ]);
      setServiceUnavailable(false);
      // Refresh conversation list if user is logged in
      if (currentUser && userToken) {
        const newConvId = payload.conversation_id || activeConvId;
        if (newConvId && newConvId !== activeConvId) setActiveConvId(newConvId);
        API.get("/api/conversations", userToken).then((list) => {
          if (Array.isArray(list)) setSavedConversations(list);
        });
      }
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "error",
          text: "I can’t reach the assistant right now. Check your connection and try again.",
        },
      ]);
      setServiceUnavailable(true);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  function useSuggestion(text) {
    setQuestion(text);
    if (window.innerWidth <= 768) {
      setSidebarOpen(false);
    }
    requestAnimationFrame(() => {
      inputRef.current?.focus();
      if (inputRef.current) {
        inputRef.current.style.height = "auto";
        inputRef.current.style.height = `${Math.max(48, Math.min(inputRef.current.scrollHeight, 180))}px`;
      }
    });
  }

  function clearConversation() {
    setMessages([]);
    setQuestion("");
    setActiveConvId(null);
    setServiceUnavailable(false);
    if (window.innerWidth <= 768) setSidebarOpen(false);
    inputRef.current?.focus();
  }

  if (currentPath === "/admin") {
    return (
      <Suspense
        fallback={
          <div
            style={{
              height: "100vh",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "#030712",
              color: "#06b6d4",
              fontFamily: "sans-serif",
            }}
          >
            Loading Admin Center...
          </div>
        }
      >
        <AdminPanel onNavigateHome={() => navigateTo("/")} />
      </Suspense>
    );
  }

  return (
    <div className="app-layout">
      {showAuthModal && (
        <AuthModal onClose={() => setShowAuthModal(false)} onSuccess={handleAuthSuccess} />
      )}

      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Modern Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`} aria-label="Assistant controls and categories">
        <div className="sidebar-brand-container">
          <a className="brand" href="/" aria-label="Seva AI Home">
            <div className="brand-mark">
              <svg viewBox="0 0 28 28" fill="none">
                <path d="M14 2 L22 6 L22 14 C22 19.5 18 23 14 24.5 C10 23 6 19.5 6 14 L6 6 Z" fill="#1e3a8a" stroke="#60a5fa" strokeWidth="1.5" strokeLinejoin="round" />
                <circle cx="14" cy="12.5" r="3" fill="#fbbf24" />
              </svg>
            </div>
            <div className="brand-text">
              <span className="brand-title">SEVA AI</span>
              <span className="brand-subtitle">Government Services</span>
            </div>
          </a>
          <button
            type="button"
            className="mobile-close-btn"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            ✕
          </button>
        </div>

        <button className="new-chat-btn" type="button" onClick={clearConversation}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>New inquiry</span>
          <kbd className="shortcut-hint">Clear</kbd>
        </button>

        <section className="sidebar-categories" aria-label="Browse categories">
          <p className="sidebar-section-title">Common Portals</p>
          <div className="category-chips">
            {CATEGORIES.map((cat) => (
              <button
                type="button"
                key={cat.name}
                className="category-btn"
                onClick={() => useSuggestion(cat.query)}
              >
                <span className="cat-icon">{cat.icon}</span>
                <span className="cat-text">{language === "kok" ? cat.kokName : cat.name}</span>
              </button>
            ))}
          </div>
        </section>

        {/* Saved Conversations (logged-in users) */}
        {currentUser && (
          <section className="conversations-history-section" aria-label="Your saved consultations">
            <p className="sidebar-section-title">YOUR CONSULTATIONS</p>
            {savedConversations.length === 0 ? (
              <p className="history-empty-hint">No saved consultations yet. Ask a question to begin!</p>
            ) : (
              <div className="conversation-list" role="list">
                {savedConversations.slice(0, 15).map((conv) => (
                  <div
                    key={conv.id}
                    role="listitem"
                    className={`conversation-item ${activeConvId === conv.id ? "active" : ""}`}
                    onClick={() => loadConversation(conv.id)}
                    tabIndex={0}
                    onKeyDown={(e) => e.key === "Enter" && loadConversation(conv.id)}
                    aria-label={"Load conversation: " + conv.title}
                  >
                    <span className="conv-icon">💬</span>
                    <span className="conv-title">{conv.title || "Consultation"}</span>
                    <button
                      type="button"
                      className="conv-delete-btn"
                      onClick={(e) => deleteConversation(conv.id, e)}
                      title="Delete conversation"
                      aria-label={"Delete: " + conv.title}
                    >✕</button>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {!currentUser && (
          <div className="guest-login-promo">
            <p className="promo-text">Sign in to save your consultations and access them later.</p>
            <button type="button" className="promo-login-btn" onClick={() => setShowAuthModal(true)}>Sign In / Register</button>
          </div>
        )}

        {/* Security & Privacy Assurance Card */}
        <section className="sidebar-security-card" aria-label="Privacy guarantee">
          <div className="security-card-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <strong>Private &amp; Secure</strong>
          </div>
          <p>Questions are processed in-memory. No chat logs are permanently stored on server disks.</p>
          <div className="security-tag">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>Verified Official Corpus</span>
          </div>
        </section>

        <footer className="sidebar-footer">
          <p>Direct citizen assistance grounded in government documentation.</p>
        </footer>
      </aside>

      {/* Main Chat Panel */}
      <section className="chat-panel" aria-label="Government services consultation">
        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="menu-toggle-btn"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar menu"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <div className="topbar-title-group">
              <span className="topbar-badge">OFFICIAL-SOURCE RAG</span>
              <h1 className="topbar-heading">National &amp; Goa Government Services</h1>
            </div>
          </div>

          <div className="topbar-actions">
            {/* Multilingual Switcher */}
            <div className="language-selector" role="group" aria-label="Select Assistant Language">
              <button
                className={`lang-btn ${language === "en" ? "active" : ""}`}
                type="button"
                onClick={() => setLanguage("en")}
                aria-pressed={language === "en"}
              >
                English
              </button>
              <button
                className={`lang-btn ${language === "kok" ? "active" : ""}`}
                type="button"
                onClick={() => setLanguage("kok")}
                aria-pressed={language === "kok"}
              >
                कोंकणी
              </button>
            </div>

            {/* Operational Admin Button */}
            <button
              type="button"
              className="topbar-admin-btn"
              onClick={() => navigateTo("/admin")}
              title="Operational Admin Center (/admin)"
              style={{
                background: "rgba(6, 182, 212, 0.12)",
                border: "1px solid rgba(6, 182, 212, 0.4)",
                color: "#06b6d4",
                padding: "6px 12px",
                borderRadius: "8px",
                fontSize: "12px",
                fontWeight: "700",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
              }}
            >
              <span>🛡️</span> Admin
            </button>

            {/* Dark / Light Mode Toggle */}
            <button
              type="button"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              aria-label="Toggle visual theme"
            >
              {theme === "dark" ? (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              )}
            </button>

            {/* Service Status */}
            <div className={`status-pill ${serviceUnavailable ? "offline" : "online"}`}>
              <span className="status-dot" />
              <span>{serviceUnavailable ? "Service Offline" : "System Ready"}</span>
            </div>

            {/* User Auth */}
            {currentUser ? (
              <div className="user-profile-badge" aria-label={"Signed in as " + currentUser.full_name}>
                <span className="user-name-tag">{currentUser.full_name || currentUser.username}</span>
                <span className={"role-pill " + (currentUser.role === "admin" ? "admin" : "user")}>
                  {currentUser.role === "admin" ? "ADMIN" : "USER"}
                </span>
                <button type="button" className="logout-btn" onClick={handleSignOut} aria-label="Sign out">
                  Sign Out
                </button>
              </div>
            ) : (
              <button type="button" className="signin-header-btn" onClick={() => setShowAuthModal(true)} aria-label="Sign in to save chats">
                Sign In
              </button>
            )}
          </div>
        </header>

        {/* Conversation Stream */}
        <main
          className="conversation-stream"
          ref={conversationRef}
          aria-live="polite"
          aria-label="Conversation messages"
        >
          {messages.length === 0 && (
            <Welcome onSuggestion={useSuggestion} language={language} />
          )}

          {messages.map((message) => (
            <Message message={message} key={message.id} />
          ))}

          {isLoading && (
            <Message
              message={{
                role: "typing",
                text: language === "kok" ? "अधिकृत सरकारी नोंदी तपासत आसा…" : "Consulting official government registers…",
              }}
            />
          )}
        </main>

        {/* Composer Area */}
        <footer className="composer-area">
          {/* Security & PII Safeguard Notice */}
          <div className="security-notice-banner" role="note">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>
              <strong>Privacy Protection:</strong> Never share Aadhaar, PAN, passwords, OTPs, or bank account details.
            </span>
          </div>

          <form className="composer-box" onSubmit={submit} noValidate>
            <label className="sr-only" htmlFor="messageInput">
              Ask a question about government schemes
            </label>
            <textarea
              ref={inputRef}
              id="messageInput"
              rows="1"
              maxLength={MAX_CHARS}
              value={question}
              disabled={isLoading}
              onChange={(event) => setQuestion(event.target.value)}
              onInput={resizeInput}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  submit(event);
                }
              }}
              placeholder={
                language === "kok"
                  ? "सरकारी योजनेविसीं, शिष्यवृत्तीविसीं विचारात…"
                  : "Ask about central or Goa government schemes, eligibility, scholarships…"
              }
              required
            />

            <div className="composer-toolbar">
              {question.length > 0 && (
                <span className={`char-counter ${question.length > 1800 ? "limit-near" : ""}`}>
                  {question.length}/{MAX_CHARS}
                </span>
              )}

              {question.length > 0 && (
                <button
                  type="button"
                  className="clear-input-btn"
                  onClick={() => setQuestion("")}
                  title="Clear text"
                  aria-label="Clear input"
                >
                  ✕
                </button>
              )}

              <button
                className="send-button"
                type="submit"
                aria-label="Send query"
                disabled={isLoading || !question.trim()}
              >
                {isLoading ? (
                  <svg className="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" strokeDasharray="31.4" strokeDashoffset="10" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="19" x2="12" y2="5" />
                    <polyline points="5 12 12 5 19 12" />
                  </svg>
                )}
              </button>
            </div>
          </form>

          <p className="legal-disclaimer">
            Seva AI is an automated information assistant grounded in verified government repositories. Always confirm final requirements with official department portals.
          </p>
        </footer>
      </section>
    </div>
  );
}

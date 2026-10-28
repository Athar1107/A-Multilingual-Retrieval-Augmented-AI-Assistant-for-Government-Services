import { useEffect, useRef, useState } from "react";

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
              <span className={`grounding-badge ${message.route === "fallback" ? "caution" : "verified"}`}>
                {message.route === "fallback" ? (
                  <>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                      <line x1="12" y1="9" x2="12" y2="13" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                    Verify with official portal
                  </>
                ) : (
                  <>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      <path d="m9 12 2 2 4-4" />
                    </svg>
                    {Math.round(message.confidence * 100)}% Source Grounded
                  </>
                )}
              </span>
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

export default function App() {
  const [language, setLanguage] = useState("en");
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [serviceUnavailable, setServiceUnavailable] = useState(false);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("seva_theme") || "dark";
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const inputRef = useRef(null);
  const conversationRef = useRef(null);

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

  function toggleTheme() {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }

  function resizeInput(event) {
    const input = event.currentTarget;
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
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
    if (inputRef.current) inputRef.current.style.height = "auto";
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", text },
    ]);
    setIsLoading(true);

    try {
      const response = await fetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ text, language }),
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
        inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 180)}px`;
      }
    });
  }

  function clearConversation() {
    setMessages([]);
    setQuestion("");
    setServiceUnavailable(false);
    if (window.innerWidth <= 768) setSidebarOpen(false);
    inputRef.current?.focus();
  }

  return (
    <div className="app-layout">
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

import React, { useState, useRef, useEffect, useCallback } from "react";
import Login from "./Login";
import LeadsView from "./LeadsView";
import ApprovalsView from "./ApprovalsView";
import {
  sendMessage,
  clearTokens,
  getToken,
  fetchAnalyticsSummary,
  fetchIntentDistribution,
  fetchLeadsOverTime,
  fetchLeadStatusBreakdown,
} from "./services/api";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell,
} from "recharts";
import "./App.css";

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4"];

// ── Small reusable components ─────────────────────────────────────────────────
const KpiCard = ({ icon, label, value, sub, color }) => (
  <div className="kpi-card" style={{ borderColor: color }}>
    <span className="kpi-icon">{icon}</span>
    <div>
      <div className="kpi-value" style={{ color }}>{value}</div>
      <div className="kpi-label">{label}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  </div>
);

const TypingDots = () => (
  <div className="typing-dots">
    <span /><span /><span />
  </div>
);

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [view, setView] = useState("chat");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", content: "👋 Hi! I'm your AI Sales Assistant. Try asking me to create a lead, show leads, or update a contact.", time: now() },
  ]);
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [intentData, setIntentData] = useState([]);
  const [leadsOverTime, setLeadsOT] = useState([]);
  const [statusData, setStatusData] = useState([]);
  const [analyticsLoading, setAL] = useState(false);
  const chatEndRef = useRef(null);

  function now() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  // ── Load analytics from backend ────────────────────────────────────────────
  const loadAnalytics = useCallback(async () => {
    setAL(true);
    try {
      const [summary, intents, lots, status] = await Promise.all([
        fetchAnalyticsSummary(),
        fetchIntentDistribution(),
        fetchLeadsOverTime(),
        fetchLeadStatusBreakdown(),
      ]);
      setAnalytics(summary);

      const intentsArr = Array.isArray(intents) ? intents : (intents?.intent_distribution || []);
      setIntentData(intentsArr.map(d => ({ name: d.intent, value: d.count })));

      const lotsArr = Array.isArray(lots) ? lots : (lots?.leads_over_time || []);
      setLeadsOT(lotsArr.map(d => ({ date: d.date?.slice(5), leads: d.count })));

      const statusArr = Array.isArray(status) ? status : (status?.status_breakdown || []);
      setStatusData(statusArr.map(d => ({ name: d.status, value: d.count })));
    } catch (e) {
      console.error("Analytics fetch failed:", e.message);
    }
    setAL(false);
  }, []);

  useEffect(() => {
    if (authed && view === "analytics") loadAnalytics();
  }, [authed, view, loadAnalytics]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Chat ───────────────────────────────────────────────────────────────────
  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setMessages(m => [...m, { role: "user", content: text, time: now() }]);
    setLoading(true);

    try {
      const res = await sendMessage(text);
      const reply = res?.result?.message || res?.result?.leads
        ? formatLeadsReply(res.result)
        : (res?.result?.error || res?.error || "Done.");
      setMessages(m => [...m, { role: "assistant", content: reply, intent: res?.intent, time: now() }]);
    } catch (err) {
      setMessages(m => [...m, { role: "assistant", content: `❌ ${err.message}`, time: now() }]);
    }
    setLoading(false);
  };

  const formatLeadsReply = (result) => {
    if (result.message) return result.message;
    if (result.leads && result.leads.length > 0) {
      return `Found ${result.total} lead(s):\n` +
        result.leads.map(l => `• ${l.email}${l.name ? ` (${l.name})` : ""} — ${l.status}`).join("\n");
    }
    return "No leads found.";
  };

  const handleLogout = () => { clearTokens(); setAuthed(false); };

  // ── Auth gate ──────────────────────────────────────────────────────────────
  if (!authed) return <Login onLogin={() => setAuthed(true)} />;

  // ── Sidebar nav items ──────────────────────────────────────────────────────
  const navItems = [
    { id: "chat", icon: "💬", label: "Chat" },
    { id: "leads", icon: "👤", label: "Leads" },
    { id: "approvals", icon: "🛡️", label: "Approvals" },
    { id: "analytics", icon: "📊", label: "Analytics" },
  ];

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <img src="/images/robot-logo.png" alt="AI Sales Robot" className="brand-icon-img" />
          <span className="brand-name">AI Sales</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(n => (
            <button
              key={n.id}
              id={`nav-${n.id}`}
              className={`nav-btn ${view === n.id ? "active" : ""}`}
              onClick={() => setView(n.id)}
            >
              <span>{n.icon}</span> {n.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-badge">
            <span className="user-dot" />
            <span className="user-label">Online</span>
          </div>
          <button id="btn-logout" className="logout-btn" onClick={handleLogout}>Sign Out</button>
        </div>
      </aside>

      {/* Main content */}
      <main className="main">
        {view === "chat" && (
          <div className="chat-wrapper">
            <div className="chat-header">
              <h2>💬 Chat</h2>
              <p className="chat-hint">Try: <em>"Create a lead for alice@acme.com"</em> · <em>"Show all leads"</em></p>
            </div>

            <div className="chat-messages" id="chat-messages">
              {messages.map((msg, i) => (
                <div key={i} className={`msg ${msg.role === "user" ? "msg-user" : "msg-bot"}`}>
                  {msg.role === "assistant" && (
                    <div className="msg-avatar">🤖</div>
                  )}
                  <div className="msg-bubble">
                    <pre className="msg-text">{msg.content}</pre>
                    <div className="msg-meta">
                      {msg.intent && <span className="intent-tag">{msg.intent}</span>}
                      <span className="msg-time">{msg.time}</span>
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="msg msg-bot">
                  <div className="msg-avatar">🤖</div>
                  <div className="msg-bubble"><TypingDots /></div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="chat-input-row">
              <input
                id="chat-input"
                className="chat-input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSend()}
                placeholder="Type a lead action or question..."
                disabled={loading}
              />
              <button id="chat-send" className="send-btn" onClick={handleSend} disabled={loading}>
                {loading ? "…" : "Send ↗"}
              </button>
            </div>
          </div>
        )}

        {view === "leads" && (
          <LeadsView />
        )}

        {view === "approvals" && (
          <ApprovalsView />
        )}

        {view === "analytics" && (
          <div className="analytics-wrapper">
            <div className="analytics-header">
              <h2>📊 Analytics Dashboard</h2>
              <button id="btn-refresh" className="refresh-btn" onClick={loadAnalytics} disabled={analyticsLoading}>
                {analyticsLoading ? "Loading…" : "↻ Refresh"}
              </button>
            </div>

            {analyticsLoading && <div className="loading-bar" />}

            {/* KPI row */}
            {analytics && (
              <div className="kpi-row">
                <KpiCard icon="👤" label="Total Leads" value={analytics.total_leads} color="#6366f1" />
                <KpiCard icon="💬" label="Total Chats" value={analytics.total_chats} color="#22c55e" />
                <KpiCard icon="✅" label="Qualified" value={analytics.qualified_leads} color="#f59e0b" />
                <KpiCard icon="📈" label="Conversion Rate"
                  value={analytics.total_leads ? `${Math.round((analytics.qualified_leads / analytics.total_leads) * 100)}%` : "0%"}
                  color="#06b6d4"
                />
              </div>
            )}

            <div className="charts-grid">
              {/* Leads over time */}
              <div className="chart-card">
                <h3>📅 Leads Over Time (30 days)</h3>
                {leadsOverTime.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={leadsOverTime}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                      <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} allowDecimals={false} />
                      <Tooltip contentStyle={{ background: "#1e293b", border: "none", borderRadius: 8 }} />
                      <Line type="monotone" dataKey="leads" stroke="#6366f1" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : <div className="no-data">No lead data yet. Create some leads!</div>}
              </div>

              {/* Intent distribution */}
              <div className="chart-card">
                <h3>🧠 Intent Distribution</h3>
                {intentData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={intentData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                        {intentData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip contentStyle={{ background: "#1e293b", border: "none", borderRadius: 8 }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : <div className="no-data">No chat history yet. Try the Chat tab!</div>}
              </div>

              {/* Lead status breakdown */}
              <div className="chart-card">
                <h3>📦 Lead Status Breakdown</h3>
                {statusData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={statusData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                      <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} allowDecimals={false} />
                      <Tooltip contentStyle={{ background: "#1e293b", border: "none", borderRadius: 8 }} />
                      <Bar dataKey="value" fill="#22c55e" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <div className="no-data">No lead statuses yet.</div>}
              </div>

              {/* AI insight */}
              {analytics && (
                <div className="chart-card insight-card">
                  <h3>🤖 AI Insight</h3>
                  <p>
                    {analytics.total_leads === 0
                      ? "Get started by creating your first lead in the Chat tab."
                      : analytics.qualified_leads / analytics.total_leads > 0.5
                        ? "🎉 Strong conversion rate! Over half your leads are qualified."
                        : analytics.qualified_leads > 0
                          ? "📈 Good progress. Focus on qualifying more leads to improve conversion."
                          : "💡 None of your leads are qualified yet. Try updating lead statuses via chat."}
                  </p>
                  <div className="insight-stats">
                    <span>Total leads: <strong>{analytics.total_leads}</strong></span>
                    <span>Qualified: <strong>{analytics.qualified_leads}</strong></span>
                    <span>Chats: <strong>{analytics.total_chats}</strong></span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
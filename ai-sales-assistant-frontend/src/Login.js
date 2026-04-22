import React, { useState } from "react";
import { loginUser, registerUser } from "./services/api";
import "./Login.css";

const Login = ({ onLogin }) => {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async () => {
    if (!email || !password) { setError("Please fill in all fields"); return; }
    setLoading(true); setError(""); setSuccess("");

    try {
      if (mode === "login") {
        await loginUser(email, password);
        onLogin();
      } else {
        await registerUser(email, password);
        setSuccess("Account created! Please sign in.");
        setMode("login");
        setPassword("");
      }
    } catch (err) {
      setError(err.message || "Server error");
    }

    setLoading(false);
  };

  const handleKey = (e) => e.key === "Enter" && handleSubmit();

  return (
    <div className="login-bg">
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <img src="/images/robot-logo.png" alt="AI Sales Robot" className="logo-icon-img" />
          <h1>AI Sales Assistant</h1>
          <p className="login-subtitle">Your AI-powered revenue engine</p>
        </div>

        {/* Mode toggle */}
        <div className="login-tabs">
          <button
            className={mode === "login" ? "tab active" : "tab"}
            onClick={() => { setMode("login"); setError(""); setSuccess(""); }}
          >Sign In</button>
          <button
            className={mode === "register" ? "tab active" : "tab"}
            onClick={() => { setMode("register"); setError(""); setSuccess(""); }}
          >Create Account</button>
        </div>

        {/* Inputs */}
        <input
          type="email"
          id="login-email"
          placeholder="Email address"
          value={email}
          onChange={e => setEmail(e.target.value)}
          onKeyDown={handleKey}
          autoComplete="email"
        />
        <input
          type="password"
          id="login-password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyDown={handleKey}
          autoComplete={mode === "login" ? "current-password" : "new-password"}
        />

        {error && <div className="login-error">⚠ {error}</div>}
        {success && <div className="login-success">✓ {success}</div>}

        <button id="login-submit" className="login-btn" onClick={handleSubmit} disabled={loading}>
          {loading ? <span className="spinner" /> : (mode === "login" ? "Sign In →" : "Create Account →")}
        </button>

        <p className="login-footer">
          Secured with JWT · bcrypt · Rate limiting
        </p>
      </div>
    </div>
  );
};

export default Login;
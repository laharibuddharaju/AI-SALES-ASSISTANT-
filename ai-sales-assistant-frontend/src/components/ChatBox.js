import React, { useState, useRef, useEffect } from "react";

const ChatBox = () => {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const suggestions = [
    "Give numeric data",
    "Summarize this",
    "Explain simply",
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const autoResize = () => {
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height =
      textareaRef.current.scrollHeight + "px";
  };

  // 🎤 Voice input (unchanged logic)
  const startVoiceInput = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech Recognition not supported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setMessage(transcript);
    };

    recognition.start();
    recognitionRef.current = recognition;
  };

  // 📤 Send message (API untouched)
  const sendMessage = async (text) => {
    const msg = text || message;

    if (!msg.trim() || loading) return;

    const userMsg = {
      role: "user",
      content: msg,
      time: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setMessage("");
    setLoading(true);
    setError("");

    try {
      const API_BASE = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000/api/v1";
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: "1",
          channel: "chat",
          message: msg,
        }),
      });

      const data = await res.json();

      const botMsg = {
        role: "bot",
        content: JSON.stringify(data.result, null, 2),
        time: new Date(),
      };

      setMessages((prev) => [...prev, botMsg]);

    } catch (error) {
      setError("Backend not reachable");
    }

    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => setMessages([]);

  const copyText = (text) => navigator.clipboard.writeText(text);

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h3>🤖 AI Sales Assistant</h3>
        <button onClick={clearChat} style={styles.clearBtn}>
          Clear
        </button>
      </div>

      {/* Messages */}
      <div style={styles.chatArea}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              justifyContent:
                msg.role === "user" ? "flex-end" : "flex-start",
              marginBottom: "10px",
            }}
          >
            <div
              style={{
                ...styles.bubble,
                background:
                  msg.role === "user" ? "#007bff" : "#f1f1f1",
                color: msg.role === "user" ? "white" : "black",
              }}
            >
              <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                {msg.content}
              </pre>

              <div style={styles.timestamp}>
                {msg.time.toLocaleTimeString()}
                {msg.role === "bot" && (
                  <span
                    onClick={() => copyText(msg.content)}
                    style={styles.copyBtn}
                  >
                    Copy
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ color: "#777", marginBottom: "10px" }}>
            AI is typing...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && <div style={{ color: "red" }}>{error}</div>}

      {/* Suggestions */}
      <div style={styles.suggestions}>
        {suggestions.map((s, i) => (
          <button
            key={i}
            style={styles.suggestionBtn}
            onClick={() => sendMessage(s)}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input */}
      <div style={styles.inputArea}>
        <button onClick={startVoiceInput} style={styles.voiceBtn}>
          🎤
        </button>

        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            autoResize();
          }}
          onKeyDown={handleKeyDown}
          placeholder="Type message..."
          style={styles.textarea}
          rows={1}
        />

        <button
          onClick={() => sendMessage()}
          disabled={!message.trim() || loading}
          style={styles.sendBtn}
        >
          ➤
        </button>
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: "700px",
    margin: "auto",
    border: "1px solid #ddd",
    borderRadius: "10px",
    display: "flex",
    flexDirection: "column",
    height: "90vh",
  },
  header: {
    padding: "10px",
    borderBottom: "1px solid #eee",
    display: "flex",
    justifyContent: "space-between",
  },
  chatArea: {
    flex: 1,
    overflowY: "auto",
    padding: "15px",
  },
  bubble: {
    padding: "10px",
    borderRadius: "15px",
    maxWidth: "70%",
  },
  timestamp: {
    fontSize: "10px",
    marginTop: "5px",
    opacity: 0.6,
    display: "flex",
    justifyContent: "space-between",
  },
  copyBtn: {
    marginLeft: "10px",
    cursor: "pointer",
    fontSize: "10px",
  },
  inputArea: {
    display: "flex",
    padding: "10px",
    borderTop: "1px solid #eee",
    gap: "10px",
  },
  textarea: {
    flex: 1,
    resize: "none",
    padding: "8px",
    borderRadius: "8px",
    border: "1px solid #ccc",
  },
  sendBtn: {
    padding: "8px 12px",
    cursor: "pointer",
  },
  voiceBtn: {
    padding: "8px",
    cursor: "pointer",
  },
  clearBtn: {
    cursor: "pointer",
  },
  suggestions: {
    padding: "5px",
    display: "flex",
    gap: "5px",
    flexWrap: "wrap",
  },
  suggestionBtn: {
    fontSize: "12px",
    padding: "5px 10px",
    cursor: "pointer",
  },
};

export default ChatBox;

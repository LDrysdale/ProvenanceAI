import React, { useState, useRef, useEffect } from "react";
import "./Chat.css";

export default function Chat() {
  const [chatSessions, setChatSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [prompt, setPrompt] = useState("");
  const endRef = useRef(null);

  const activeSession = chatSessions.find((s) => s.id === activeSessionId);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeSession]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    const newMessage = {
      question: prompt,
      response: `Creative reply to: "${prompt}"`,
    };

    if (!activeSessionId) {
      const newSession = {
        id: Date.now().toString(),
        title: prompt.length > 20 ? prompt.slice(0, 17) + "..." : prompt,
        messages: [newMessage],
      };
      setChatSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
    } else {
      setChatSessions((prev) =>
        prev.map((session) =>
          session.id === activeSessionId
            ? {
                ...session,
                messages: [...session.messages, newMessage],
              }
            : session
        )
      );
    }
    setPrompt("");
  };

  const handleSelectSession = (id) => {
    setActiveSessionId(id);
  };

  return (
    <div className="app-container">
      {/* Left sidebar */}
      <aside className="sidebar">
        <div className="menu-dot" title="Menu">
          ☰
        </div>
        <h2 className="sidebar-title">Chat History</h2>
        {chatSessions.length === 0 && (
          <p className="no-chats-text">No chats yet. Start a new chat!</p>
        )}
        <ul className="session-list">
          {chatSessions.map((session) => (
            <li
              key={session.id}
              className={`session-item ${
                session.id === activeSessionId ? "active-session" : ""
              }`}
              onClick={() => handleSelectSession(session.id)}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSelectSession(session.id);
              }}
              aria-selected={session.id === activeSessionId}
              role="button"
            >
              {session.title}
            </li>
          ))}
        </ul>
      </aside>

      {/* Center chat container */}
      <main className="main-chat-container">
        {!activeSession ? (
          <>
            <h1 className="main-title">Welcome! Start a new chat</h1>
            <form className="initial-form" onSubmit={handleSubmit}>
              <textarea
                rows={4}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Type your prompt here..."
                className="prompt-textarea"
                spellCheck={false}
              />
              <button type="submit" className="btn-submit">
                Submit
              </button>
            </form>
          </>
        ) : (
          <>
            <div
              className="chat-messages"
              role="log"
              aria-live="polite"
              aria-relevant="additions"
            >
              {activeSession.messages.map(({ question, response }, idx) => (
                <div key={idx} className="message-row">
                  <div className="chat-bubble user-bubble">{question}</div>
                  <div className="chat-bubble bot-bubble">{response}</div>
                </div>
              ))}
              <div ref={endRef} />
            </div>

            <form className="input-form" onSubmit={handleSubmit}>
              <textarea
                rows={2}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Continue the conversation..."
                className="prompt-textarea chatgpt-style-input"
                spellCheck={false}
              />
              <button type="submit" className="btn-send">
                Send
              </button>
            </form>
          </>
        )}
      </main>
    </div>
  );
}

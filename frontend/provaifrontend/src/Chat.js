// frontend/provaifrontend/src/Chat.js
import React, { useState, useRef, useEffect } from "react";
import { FaPlus, FaSignInAlt, FaSignOutAlt } from "react-icons/fa";
import {
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
} from "firebase/auth";
import { auth } from "./firebase";
import "./Chat.css";
import logo from "./logo.svg";

export default function Chat() {
  const [user, setUser] = useState(null);
  const [chatSessions, setChatSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [timelineExpanded, setTimelineExpanded] = useState(false);
  const [connectors, setConnectors] = useState([]);

  const endRef = useRef(null);
  const cardsRef = useRef([]);

  const [contextMenu, setContextMenu] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);

  const activeSession = chatSessions.find((s) => s.id === activeSessionId);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", inline: "end" });
  }, [activeSession]);

  const updateConnectors = () => {
    if (!activeSession) return;

    const newConnectors = [];
    for (let i = 0; i < activeSession.messages.length - 1; i++) {
      const current = cardsRef.current[i];
      const next = cardsRef.current[i + 1];
      if (current && next) {
        const top = current.offsetTop + current.offsetHeight / 2 - 1;
        const left = current.offsetLeft + current.offsetWidth;
        const width = next.offsetLeft - left;
        newConnectors.push({ top, left, width });
      }
    }
    setConnectors(newConnectors);
  };

  useEffect(() => {
    updateConnectors();
  }, [activeSession, timelineExpanded, prompt]);

  useEffect(() => {
    const handleResize = () => updateConnectors();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [activeSession]);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
    });
    return () => unsubscribe();
  }, []);

  const handleLogin = async () => {
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
    } catch (err) {
      console.error("Login failed:", err);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    const newMessage = {
      question: prompt,
      response: `Creative reply to: "${prompt}"`,
      timestamp: new Date().toLocaleString([], {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }),
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
                title:
                  session.messages.length === 0
                    ? prompt.length > 20
                      ? prompt.slice(0, 17) + "..."
                      : prompt
                    : session.title,
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

  const handleNewChat = () => {
    const newSession = {
      id: Date.now().toString(),
      title: "New Chat",
      messages: [],
    };
    setChatSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
  };

  const handleRightClick = (e, sessionId) => {
    e.preventDefault();
    setContextMenu({
      x: e.pageX,
      y: e.pageY,
      sessionId,
    });
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
    setSessionToDelete(contextMenu?.sessionId);
    setContextMenu(null);
  };

  const handleConfirmDelete = async () => {
    if (!sessionToDelete || !user) return;

    setChatSessions((prev) => prev.filter((s) => s.id !== sessionToDelete));
    if (activeSessionId === sessionToDelete) setActiveSessionId(null);

    try {
      await fetch("/api/delete_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.uid,
          session_id: sessionToDelete,
        }),
      });
    } catch (err) {
      console.error("Failed to delete remotely:", err);
    }

    setShowDeleteConfirm(false);
    setSessionToDelete(null);
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
    setSessionToDelete(null);
  };

  return (
    <div className="chat-app">
      <header className="chat-header">
        <div className="logo-circle">
          <img src={logo} alt="Logo" />
        </div>
        Chat Timeline Interface
        <div
          className="auth-icon"
          onClick={user ? handleLogout : handleLogin}
          title={user ? "Logout" : "Login"}
        >
          {user ? <FaSignOutAlt size={20} /> : <FaSignInAlt size={20} />}
        </div>
      </header>

      <main className={`timeline-container ${timelineExpanded ? "expanded" : ""}`}>
        <div
          className="timeline-overlay"
          onClick={() => setTimelineExpanded(!timelineExpanded)}
        >
          {activeSession && (
            <div
              className="timeline-scroll"
              role="log"
              aria-live="polite"
              style={{ position: "relative" }}
            >
              {activeSession.messages.map(({ question, response, timestamp }, idx) => (
                <div
                  className="timeline-card"
                  key={idx}
                  ref={(el) => (cardsRef.current[idx] = el)}
                >
                  <div className="timestamp">{timestamp}</div>
                  <div className="question">{question}</div>
                  <div className="answer">{response}</div>
                </div>
              ))}
              {connectors.map(({ top, left, width }, i) => (
                <div
                  key={`connector-${i}`}
                  className="connector-line"
                  style={{
                    top,
                    left,
                    width,
                  }}
                />
              ))}
              <div ref={endRef} />
            </div>
          )}
        </div>
      </main>

      <form className="prompt-form" onSubmit={handleSubmit}>
        <div className="input-button-wrapper">
          <button
            type="button"
            className="new-chat-icon-button"
            onClick={handleNewChat}
            title="New Chat"
          >
            <FaPlus />
          </button>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask something..."
            rows={2}
            className="prompt-input"
          />
          <button type="submit" className="submit-button">Send</button>
        </div>
      </form>

      <section className="chat-history-scroll">
        {chatSessions.map((session) => (
          <div
            key={session.id}
            className={`chat-capsule ${session.id === activeSessionId ? "active" : ""}`}
            onClick={() => handleSelectSession(session.id)}
            onContextMenu={(e) => handleRightClick(e, session.id)}
          >
            <div className="capsule-title">{session.title}</div>
            <div className="capsule-stats">
              <span>{session.messages.length} Questions</span>
            </div>
          </div>
        ))}
      </section>

      {contextMenu && (
        <div
          className="context-menu"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <div className="context-menu-item" onClick={handleDeleteClick}>
            Delete
          </div>
        </div>
      )}

      {showDeleteConfirm && (
        <div className="confirm-popup">
          <div className="confirm-box">
            <p>Are you sure you want to delete?</p>
            <div className="confirm-buttons">
              <button onClick={handleConfirmDelete}>Yes</button>
              <button onClick={handleCancelDelete}>No</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

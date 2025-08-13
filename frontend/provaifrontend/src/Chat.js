import React, { useState, useRef, useEffect, useCallback } from "react";
import { FaPlus } from "react-icons/fa";
import "./Chat.css";
import TopOfPage from "./components/TopOfPage";
import useDragAndDrop from "./components/clickanddrag";
import { auth } from './firebase'; // import your Firebase auth instance



export default function Chat() {
  const [chatSessions, setChatSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [timelineExpanded, setTimelineExpanded] = useState(false);
  const [connectors, setConnectors] = useState([]);

  const endRef = useRef(null);
  const cardsRef = useRef([]);
  const scrollRef = useRef(null);
  useDragAndDrop(scrollRef);

  const [contextMenu, setContextMenu] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);

  const activeSession = chatSessions.find((s) => s.id === activeSessionId);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", inline: "end" });
  }, [activeSession]);

  const updateConnectors = useCallback(() => {
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
  }, [activeSession]);

  useEffect(() => {
    updateConnectors();
  }, [updateConnectors, timelineExpanded, prompt]);

  useEffect(() => {
    const handleResize = () => updateConnectors();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [updateConnectors]);

  const handleSubmit = async (e) => {
  e.preventDefault();
  if (!prompt.trim()) return;

  try {
    const user = auth.currentUser;
    if (!user) {
      alert("Please sign in first.");
      return;
    }

    const token = await user.getIdToken(true); // get fresh Firebase ID token

    const currentSession = chatSessions.find(s => s.id === activeSessionId);
    const chat_id = currentSession ? currentSession.id : null;
    const chat_subject = currentSession ? currentSession.title : "General";

    const res = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,  // Include the token here
      },
      body: JSON.stringify({
        message: prompt,
        context: "",
        chat_id,
        chat_subject,
      }),
    });

    if (!res.ok) {
      throw new Error(`Backend error: ${res.statusText}`);
    }

    const data = await res.json();

    const newMessage = {
      question: data.message,
      response: data.response,
      timestamp: new Date().toLocaleString([], {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    if (!activeSessionId || !currentSession) {
      const newSession = {
        id: data.chat_id,
        title: data.chat_subject || (prompt.length > 20 ? prompt.slice(0, 17) + "..." : prompt),
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
  } catch (error) {
    console.error("Error submitting prompt:", error);
  }
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

  const handleConfirmDelete = () => {
    setChatSessions((prev) => prev.filter((s) => s.id !== sessionToDelete));
    if (activeSessionId === sessionToDelete) setActiveSessionId(null);
    setShowDeleteConfirm(false);
    setSessionToDelete(null);
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
    setSessionToDelete(null);
  };

  return (
    <div className="chat-app">
      <TopOfPage />

      <main className={`timeline-container ${timelineExpanded ? "expanded" : ""}`}>
        <div
          className="timeline-overlay"
          onClick={() => setTimelineExpanded(!timelineExpanded)}
          ref={scrollRef}
        >
          {activeSession && (
            <div className="timeline-scroll" role="log" aria-live="polite" style={{ position: "relative" }}>
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
                  style={{ top, left, width }}
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
          <div className="context-menu-item" onClick={handleDeleteClick}>Delete</div>
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

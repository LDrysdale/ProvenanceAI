import React, { useState, useRef, useEffect, useCallback } from "react";
import { FaPlus } from "react-icons/fa";
import "./Chat.css";
import TopOfPage from "./components/TopOfPage";
import useDragAndDrop from "./components/clickanddrag";

import { Eye, EyeOff, RadioTower, NotebookText, Hourglass, Brain, Dumbbell, MessageCircleHeart, Bot, ArrowBigUpDash } from "lucide-react"; // 👁️ + new icons

export default function Chat() {
  const [chatSessions, setChatSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [timelineExpanded, setTimelineExpanded] = useState(false);
  const [connectors, setConnectors] = useState([]);
  const [selectedSquare, setSelectedSquare] = useState(null);

  const [focusedCard, setFocusedCard] = useState(null); /* Focus Card Addition */
  const toggleFocus = (id) => {
    setFocusedCard(focusedCard === id ? null : id);
  };

  const endRef = useRef(null);
  const cardsRef = useRef([]);
  const scrollRef = useRef(null);
  useDragAndDrop(scrollRef);

  const [contextMenu, setContextMenu] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);

  const activeSession = chatSessions.find((s) => s.id === activeSessionId);

  const [selectedLeftSquare, setSelectedLeftSquare] = useState(null);
  const [selectedRightSquare, setSelectedRightSquare] = useState(null);

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
        const startX = current.offsetLeft + current.offsetWidth;
        const startY = current.offsetTop + current.offsetHeight / 2;

        const endX = next.offsetLeft;
        const endY = next.offsetTop + next.offsetHeight / 2;

        newConnectors.push({ startX, startY, endX, endY });
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
        <div className="timeline-overlay" ref={scrollRef}>
          {activeSession && (
            <div className="timeline-scroll" role="log" aria-live="polite" style={{ position: "relative" }}>
              {activeSession.messages.map(({ question, response, timestamp }, idx) => (
                <div
                  className={`timeline-card ${focusedCard === idx ? "focused" : ""}`}
                  key={idx}
                  ref={(el) => (cardsRef.current[idx] = el)}
                >
                  <button
                    className="focus-btn"
                    onClick={() => toggleFocus(idx)}
                  >
                    {focusedCard === idx ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>

                  <div className="timestamp">{timestamp}</div>
                  <div className="question">{question}</div>
                  <div className="answer">{response}</div>
                </div>
              ))}

              {connectors.length > 0 && (
                <svg
                  className="connector-svg"
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    pointerEvents: "none",
                    overflow: "visible"
                  }}
                >
                  {connectors.map(({ startX, startY, endX, endY }, i) => (
                    <line
                      key={`connector-${i}`}
                      x1={startX}
                      y1={startY}
                      x2={endX}
                      y2={endY}
                      stroke="#6366f1"
                      strokeWidth="2"
                    />
                  ))}
                </svg>
              )}

              <div ref={endRef} />
            </div>
          )}
        </div>

        {focusedCard !== null && (
          <div className="card-overlay" onClick={() => setFocusedCard(null)} />
        )}
      </main>

      {/* Chat history capsules */}
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

      {/* Prompt toolbar */}
      <form className="prompt-toolbar" onSubmit={handleSubmit}>
        <div className="toolbar-content">
          {/* Left third: squares with icons */}
          <div className="toolbar-left">
            <div className="toolbar-section">
              <div className="toolbar-section-title">Tools</div>
              <div className="squares-container">
                {[
                  { id: 1, label: "Ideas Generator", icon: <RadioTower size={25} /> },
                  { id: 2, label: "Momentum Manager", icon: <Hourglass size={25} /> },
                  { id: 3, label: "Business Plan Generator", icon: <NotebookText size={25} /> },
                  { id: 4, label: "Psychologist", icon: <Brain size={25} /> },
                ].map(({ id, label, icon }) => (
                  <div key={id} className="square-with-text">
                    <div
                      className={`selectable-square ${selectedLeftSquare === id ? "selected" : ""}`}
                      onClick={() =>
                        setSelectedLeftSquare(selectedLeftSquare === id ? null : id)
                      }
                      title={label}
                    >
                      {icon}
                    </div>
                    <span className="square-label">{label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>


          {/* Middle third: prompt input pill */}
          <div className="toolbar-middle">
            <div className="pill-container">
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
                rows={1}
                className="prompt-input"
              />

              <button type="submit" className="submit-button">Send</button>
            </div>
          </div>

          {/* Right third: empty */}
          <div className="toolbar-right">
            <div className="toolbar-section">
              <div className="toolbar-section-title">Coaches</div>
              <div className="squares-container">
                {[
                  { id: 1, label: "Tough Love", icon: <Dumbbell size={25} /> },
                  { id: 2, label: "Positive Pusher", icon: <ArrowBigUpDash size={25} /> },
                  { id: 3, label: "Empathy Builder", icon: <MessageCircleHeart size={25} /> },
                  { id: 4, label: "Adaptor", icon: <Bot size={25} /> },
                ].map(({ id, label, icon }) => (
                  <div key={id} className="square-with-text">
                    <div
                      className={`selectable-square ${selectedRightSquare === id ? "selected" : ""}`}
                      onClick={() =>
                        setSelectedRightSquare(selectedRightSquare === id ? null : id)
                      }
                      title={label}
                    >
                      {icon}
                    </div>
                    <span className="square-label">{label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </form>

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

import React, { useState, useRef, useEffect } from "react";
import "./Chat.css";

export default function Chat() {
  const [chatSessions, setChatSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [prompt, setPrompt] = useState("");
  const endRef = useRef(null);
  const cardsRef = useRef([]);
  const [timelineExpanded, setTimelineExpanded] = useState(false);

  const activeSession = chatSessions.find((s) => s.id === activeSessionId);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", inline: "end" });
  }, [activeSession]);

  const [connectors, setConnectors] = useState([]);

  useEffect(() => {
    if (!activeSession) return;

    const newConnectors = [];

    for (let i = 0; i < activeSession.messages.length - 1; i++) {
      const currentCard = cardsRef.current[i];
      const nextCard = cardsRef.current[i + 1];

      if (currentCard && nextCard) {
        const top = currentCard.offsetTop + currentCard.offsetHeight / 2 - 1;
        const left = currentCard.offsetLeft + currentCard.offsetWidth;
        const width = nextCard.offsetLeft - left;

        newConnectors.push({ top, left, width });
      }
    }
    setConnectors(newConnectors);
  }, [activeSession, timelineExpanded, prompt]);

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

  const getTopKeywords = (session) => {
    if (!session?.messages?.length) return [];

    const stopWords = new Set([
      "the", "is", "and", "to", "in", "of", "a", "an", "for", "on", "it", "this", "that",
      "i", "you", "with", "are", "be", "was", "at", "as", "by", "we", "our", "or", "from",
      "my", "your", "they", "have", "has", "do", "did", "what", "who", "how", "where", "when"
    ]);

    const wordCounts = {};

    session.messages.forEach((msg) => {
      const words = msg.question
        .toLowerCase()
        .replace(/[^\w\s]/g, "")
        .split(/\s+/);

      words.forEach((word) => {
        if (!stopWords.has(word) && word.length > 2) {
          wordCounts[word] = (wordCounts[word] || 0) + 1;
        }
      });
    });

    return Object.entries(wordCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([word]) => word);
  };

  return (
    <div className="chat-app">
      <header className="chat-header">Chat Timeline Interface</header>

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
                  style={{ position: "relative", whiteSpace: "normal", wordWrap: "break-word", overflowWrap: "break-word" }}
                >
                  <div className="timestamp" style={{ marginBottom: "0.5rem", position: "relative", right: 0, bottom: "auto" }}>
                    {timestamp}
                  </div>
                  <div className="question">{question}</div>
                  <div className="answer">{response}</div>
                </div>
              ))}

              {connectors.map(({ top, left, width }, i) => (
                <div
                  key={"connector-" + i}
                  style={{
                    position: "absolute",
                    top: top,
                    left: left,
                    width: width,
                    height: 2,
                    backgroundColor: "#8b91a9",
                    borderRadius: 1,
                    pointerEvents: "none",
                    zIndex: 5,
                  }}
                />
              ))}

              <div ref={endRef} />
            </div>
          )}
        </div>
      </main>

      {/* Updated form with wrapper */}
      <form className="prompt-form" onSubmit={handleSubmit}>
        <div className="input-button-wrapper">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask something..."
            rows={2}
            className="prompt-input"
          />
          <button type="submit" className="submit-button">
            Send
          </button>
        </div>
      </form>

      <section className="chat-history-scroll">
        {chatSessions.map((session) => (
          <div
            key={session.id}
            className={`chat-capsule ${session.id === activeSessionId ? "active" : ""}`}
            onClick={() => handleSelectSession(session.id)}
          >
            <div className="capsule-title">{session.title}</div>
            <div className="capsule-stats">
              <span>{session.messages.length} Questions </span>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

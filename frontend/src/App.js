import React, { useState, useRef, useEffect } from "react";

/**
 * Main application component for the creative prompt interface.
 */
export default function ChatWithImagePrompt() {
  const [chatHistory, setChatHistory] = useState([]);
  const [responses, setResponses] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [hasStarted, setHasStarted] = useState(false);
  const endRef = useRef(null);

  // Auto-scroll to bottom when chat updates
  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory, responses]);

  // Handle submitting a new prompt
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    const updatedChat = [...chatHistory, prompt];
    const simulatedResponse = `Creative reply to: "${prompt}"`;

    setChatHistory(updatedChat);
    setResponses([...responses, simulatedResponse]);
    setPrompt("");
    setHasStarted(true);
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      
      {/* --- Sidebar (Left Panel) --- */}
      <div style={{
        width: "250px",
        background: "#f0f4f8",
        borderRight: "1px solid #ccc",
        padding: "1rem",
      }}>
        {/* Large dot icon as menu */}
        <div style={{
          width: "60px",
          height: "60px",
          backgroundColor: "#3ba4dc",
          color: "white",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: "bold",
          marginBottom: "1rem",
          cursor: "pointer",
        }}>
          ☰
        </div>

        <h2 style={{ fontSize: "1rem", fontWeight: "600" }}>Your Prompts</h2>

        <ul style={{ listStyle: "none", padding: 0, marginTop: "1rem" }}>
          {chatHistory.map((item, idx) => (
            <li key={idx} style={{
              background: "#ffffff",
              marginBottom: "0.5rem",
              padding: "0.75rem",
              borderRadius: "0.5rem",
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              fontSize: "0.9rem",
            }}>
              {item}
            </li>
          ))}
        </ul>
      </div>

      {/* --- Main Panel --- */}
      <div style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: hasStarted ? "space-between" : "center",
        alignItems: "center",
        padding: hasStarted ? "1rem 2rem 6rem" : "2rem",
        overflowY: "auto",
        position: "relative"
      }}>
        {!hasStarted ? (
          <>
            <h1 style={{
              fontSize: "1.8rem",
              marginBottom: "2rem",
              fontWeight: "600"
            }}>
              Chat + Image Prompt
            </h1>

            {/* Initial centered prompt box with dot style */}
            <form onSubmit={handleSubmit} style={{
              border: "2px dotted #3ba4dc",
              borderRadius: "1rem",
              padding: "1rem",
              width: "100%",
              maxWidth: "600px",
              background: "#ffffff",
              boxShadow: "0 4px 8px rgba(0,0,0,0.05)"
            }}>
              <textarea
                rows="4"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Type your prompt here..."
                style={{
                  width: "100%",
                  border: "none",
                  outline: "none",
                  resize: "none",
                  fontSize: "1rem",
                  padding: "0.5rem",
                  background: "transparent",
                }}
              />
              <button
                type="submit"
                style={{
                  marginTop: "1rem",
                  padding: "0.75rem 1.5rem",
                  background: "#3ba4dc",
                  color: "white",
                  border: "none",
                  borderRadius: "0.75rem",
                  cursor: "pointer",
                  fontWeight: "600"
                }}
              >
                Submit
              </button>
            </form>
          </>
        ) : (
          <>
            {/* Chat bubbles layout */}
            <div style={{ width: "100%", maxWidth: "900px" }}>
              {chatHistory.map((item, idx) => (
                <div key={idx} style={{ display: "flex", marginBottom: "1.5rem" }}>
                  {/* User message on left */}
                  <div style={{
                    flex: 1,
                    background: "#ecf6ff",
                    padding: "1rem",
                    borderRadius: "1rem",
                    marginRight: "1rem",
                    boxShadow: "0 1px 4px rgba(0,0,0,0.04)"
                  }}>
                    <strong>You:</strong> {item}
                  </div>

                  {/* Response on right */}
                  <div style={{
                    flex: 1,
                    background: "#fffbe7",
                    padding: "1rem",
                    borderRadius: "1rem",
                    marginLeft: "1rem",
                    boxShadow: "0 1px 4px rgba(0,0,0,0.04)"
                  }}>
                    <strong>AI:</strong> {responses[idx]}
                  </div>
                </div>
              ))}
              <div ref={endRef} />
            </div>

            {/* Sticky bottom input */}
            <form
              onSubmit={handleSubmit}
              style={{
                position: "fixed",
                bottom: 0,
                left: "250px",
                right: 0,
                background: "#ffffff",
                borderTop: "1px solid #e0e0e0",
                padding: "1rem 2rem",
              }}
            >
              <div style={{
                maxWidth: "900px",
                margin: "0 auto",
                display: "flex",
                flexDirection: "column",
              }}>
                <textarea
                  rows="3"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Continue the conversation..."
                  style={{
                    width: "100%",
                    border: "1px solid #ccc",
                    borderRadius: "0.75rem",
                    padding: "0.75rem",
                    fontSize: "1rem",
                    resize: "none",
                  }}
                />
                <button
                  type="submit"
                  style={{
                    marginTop: "0.75rem",
                    alignSelf: "flex-end",
                    padding: "0.6rem 1.2rem",
                    background: "#3ba4dc",
                    color: "white",
                    border: "none",
                    borderRadius: "0.75rem",
                    fontWeight: "600",
                    cursor: "pointer"
                  }}
                >
                  Send
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

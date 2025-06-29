import React, { useState, useRef, useEffect } from "react";
import { getAuth, signOut } from "firebase/auth";
import { useNavigate } from "react-router-dom";

export default function ProvenanceMain() {
  const [chatHistory, setChatHistory] = useState([]);
  const [responses, setResponses] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [hasStarted, setHasStarted] = useState(false);
  const endRef = useRef(null);
  const navigate = useNavigate();

  // Scroll to the bottom of the chat whenever chat history or responses change
  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory, responses]);

  // Handle form submission for chat input
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return; // Don't submit if the prompt is empty

    const updatedChat = [...chatHistory, prompt];
    setChatHistory(updatedChat);
    setPrompt("");
    setHasStarted(true);

    try {
      let headers = { "Content-Type": "application/json" };
      
      // Check if we are using local data or Firebase authentication
      if (process.env.REACT_APP_USE_LOCAL_DATA === "1") {
        const mockToken = localStorage.getItem("mock_token");
        if (!mockToken) throw new Error("Not logged in");
        headers["Authorization"] = `Bearer ${mockToken}`;
      } else {
        const auth = getAuth();
        const user = auth.currentUser;
        if (!user) throw new Error("Not logged in");
        const idToken = await user.getIdToken();
        headers["Authorization"] = `Bearer ${idToken}`;
      }

      // Make a request to the backend to process the AI response
      const response = await fetch("/ask", {
        method: "POST",
        headers,
        body: JSON.stringify({ message: prompt }),
      });

      if (!response.ok) throw new Error(`Backend error: ${response.statusText}`);
      const data = await response.json();

      setResponses((prev) => [...prev, data.response]);
    } catch (err) {
      setResponses((prev) => [...prev, `Error: ${err.message}`]);
    }
  };

  // Handle user logout
  const handleLogout = async () => {
    try {
      const auth = getAuth();
      await signOut(auth);  // Sign out from Firebase
      localStorage.removeItem("mock_token");  // Remove mock token if present
      navigate("/");  // Redirect to login page
    } catch (err) {
      console.error("Logout error:", err.message);
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
      <h1>AI Tool</h1>
      <button
        onClick={handleLogout}
        style={{
          padding: "0.5rem 1rem",
          backgroundColor: "#FF5733",
          color: "white",
          border: "none",
          cursor: "pointer",
          marginBottom: "1rem",
        }}
      >
        Logout
      </button>

      <div style={{ background: "#f9f9f9", padding: "1rem", borderRadius: "8px", minHeight: "300px" }}>
        <div style={{ marginBottom: "1rem", maxHeight: "300px", overflowY: "auto" }}>
          {chatHistory.map((msg, index) => (
            <div key={index} style={{ padding: "0.5rem", background: "#e6f7ff", marginBottom: "0.5rem", borderRadius: "4px" }}>
              <strong>You:</strong> {msg}
            </div>
          ))}
          {responses.map((response, index) => (
            <div key={index} style={{ padding: "0.5rem", background: "#e0ffe0", marginBottom: "0.5rem", borderRadius: "4px" }}>
              <strong>AI:</strong> {response}
            </div>
          ))}
          <div ref={endRef} />
        </div>
        
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column" }}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt here..."
            rows="4"
            style={{
              padding: "0.75rem",
              marginBottom: "1rem",
              fontSize: "1rem",
              borderRadius: "8px",
              border: "1px solid #ccc",
              resize: "none",
              minHeight: "80px",
            }}
          />
          <button
            type="submit"
            style={{
              padding: "0.75rem",
              backgroundColor: "#4CAF50",
              color: "white",
              border: "none",
              cursor: "pointer",
              borderRadius: "8px",
            }}
          >
            Submit
          </button>
        </form>
      </div>
    </div>
  );
}

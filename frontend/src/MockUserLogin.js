import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function MockUserLogin() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Mock backend URL (you can replace with a real API if needed)
  const backendUrl = process.env.REACT_APP_USE_LOCAL_DATA === "1"
    ? "http://localhost:8000/api/auth/mock_login"
    : "/api/auth/mock_login";

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      // Mock login request (you can replace this with your real login)
      const response = await fetch(backendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ first_name: firstName.trim(), last_name: lastName.trim() }),
      });

      if (!response.ok) throw new Error("Invalid name or user not found");

      const data = await response.json();
      localStorage.setItem("mock_token", data.token); // Store dummy token or session
      navigate("/app");  // Redirect to the AI tool page after login
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "auto", padding: "2rem" }}>
      <h2>Mock Login</h2>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          placeholder="First Name"
          value={firstName}
          required
          onChange={(e) => setFirstName(e.target.value)}
          style={{ width: "100%", marginBottom: "1rem", padding: "0.5rem" }}
        />
        <input
          type="text"
          placeholder="Last Name"
          value={lastName}
          required
          onChange={(e) => setLastName(e.target.value)}
          style={{ width: "100%", marginBottom: "1rem", padding: "0.5rem" }}
        />
        <button type="submit" style={{ width: "100%", padding: "0.75rem" }}>
          Login
        </button>
        {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}
      </form>
    </div>
  );
}

// src/PasswordReset.js
import React, { useState } from "react";
import { sendPasswordResetEmail } from "firebase/auth";
import { auth } from "./firebase";
import { Link } from "react-router-dom";
import DotCluster from "./DotCluster";

export default function PasswordReset() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleReset = async (e) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    try {
      await sendPasswordResetEmail(auth, email);
      setMessage("Password reset email sent! Check your inbox.");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div
      style={{
        height: "100vh",
        width: "100vw",
        backgroundColor: "#ffffff",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: 16,
        boxSizing: "border-box",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          width: "90%",
          maxWidth: 400,
          aspectRatio: "3 / 4",
          zIndex: 0,
          pointerEvents: "none",
        }}
      >
        <DotCluster />
      </div>

      <div
        style={{
          backgroundColor: "white",
          borderRadius: 24,
          border: "2px solid #ccc",
          padding: 32,
          width: "90%",
          maxWidth: 400,
          boxShadow: "0 8px 16px rgba(0,0,0,0.1)",
          boxSizing: "border-box",
          textAlign: "center",
          position: "relative",
          zIndex: 1,
        }}
      >
        <img
          src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
          alt="Logo"
          style={{ height: 48, marginBottom: 24 }}
        />
        <h1 style={{ fontSize: 24, marginBottom: 8, color: "#333" }}>Reset password</h1>
        <p style={{ fontSize: 14, color: "#666", marginBottom: 24 }}>
          Enter your email to reset your password
        </p>
        <form onSubmit={handleReset} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <input
            type="email"
            value={email}
            placeholder="Enter your email"
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              padding: "12px 16px",
              borderRadius: 8,
              border: "1.5px solid #ccc",
              fontSize: 16,
              outline: "none",
            }}
          />
          <button
            type="submit"
            style={{
              backgroundColor: "#1a73e8",
              color: "white",
              fontWeight: "bold",
              padding: "12px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              fontSize: 16,
              marginTop: 8,
            }}
          >
            Send Reset Email
          </button>
          {message && (
            <p style={{ color: "green", fontSize: 14, textAlign: "center", margin: 0 }}>{message}</p>
          )}
          {error && (
            <p style={{ color: "red", fontSize: 14, textAlign: "center", margin: 0 }}>{error}</p>
          )}
        </form>
        <p style={{ marginTop: 24, fontSize: 14, color: "#444" }}>
          Back to{" "}
          <Link to="/" style={{ color: "#1a73e8", textDecoration: "none" }}>
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}

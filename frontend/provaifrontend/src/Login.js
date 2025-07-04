import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "./firebase";
import { useAuthState } from "react-firebase-hooks/auth";
import DotCluster from "./DotCluster"; // ✅ Make sure the path is correct

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [user, loading] = useAuthState(auth);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate("/chat");
  }, [user, navigate]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await signInWithEmailAndPassword(auth, email, password);
      navigate("/chat");
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading)
    return <div style={{ textAlign: "center", marginTop: 40 }}>Loading...</div>;

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
      {/* 🔵 Dynamic Dot Background */}
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

      {/* 🟦 Login Form */}
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
        <h1 style={{ fontSize: 24, marginBottom: 8, color: "#333" }}>Sign in</h1>
        <p style={{ fontSize: 14, color: "#666", marginBottom: 24 }}>Use your account</p>
        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <input
            type="email"
            value={email}
            placeholder="Email"
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
          <input
            type="password"
            value={password}
            placeholder="Password"
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{
              padding: "12px 16px",
              borderRadius: 8,
              border: "1.5px solid #ccc",
              fontSize: 16,
              outline: "none",
            }}
          />
          {error && (
            <p style={{ color: "red", fontSize: 14, margin: 0, textAlign: "center" }}>{error}</p>
          )}
          <div style={{ textAlign: "right", fontSize: 14 }}>
            <Link to="/reset-password" style={{ color: "#1a73e8", textDecoration: "none" }}>
              Forgot password?
            </Link>
          </div>
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
            Next
          </button>
        </form>
        <p style={{ marginTop: 24, fontSize: 14, color: "#444" }}>
          Don't have an account?{" "}
          <Link to="/signup" style={{ color: "#1a73e8", textDecoration: "none" }}>
            Sign up here
          </Link>
        </p>
      </div>
    </div>
  );
}

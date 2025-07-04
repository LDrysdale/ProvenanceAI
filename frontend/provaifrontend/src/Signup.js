// src/Signup.js
import React, { useState, useEffect } from "react";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { auth, db } from "./firebase";
import { useNavigate, Link } from "react-router-dom";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";
import { useAuthState } from "react-firebase-hooks/auth";
import DotCluster from "./DotCluster";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tier, setTier] = useState("free");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState(null);

  const [user, loading] = useAuthState(auth);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate("/chat");
  }, [user, navigate]);

  const handleSignup = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const uid = userCredential.user.uid;

      const now = new Date();
      let expiry;

      if (tier === "free") {
        expiry = new Date(now.setFullYear(now.getFullYear() + 100));
      } else {
        expiry = new Date(now.setFullYear(now.getFullYear() + 1));
      }

      await new Promise((resolve) => {
        const unsubscribe = auth.onAuthStateChanged(async (authUser) => {
          if (authUser && authUser.uid === uid) {
            await setDoc(doc(db, "users", uid), {
              email,
              tier,
              displayName,
              profilePicURL: "",
              subscriptionStatus: tier === "free" ? "lifetime" : "active",
              membershipExpiry: expiry.toISOString(),
              createdAt: serverTimestamp(),
            });

            unsubscribe();
            resolve();
          }
        });
      });

      navigate("/chat");
    } catch (err) {
      console.error("🔥 Error during signup or Firestore write:", err);
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
        <h1 style={{ fontSize: 24, marginBottom: 8, color: "#333" }}>Create account</h1>
        <p style={{ fontSize: 14, color: "#666", marginBottom: 24 }}>
          Sign up to get started
        </p>
        <form onSubmit={handleSignup} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <input
            type="text"
            value={displayName}
            placeholder="Display Name"
            onChange={(e) => setDisplayName(e.target.value)}
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
          <select
            value={tier}
            onChange={(e) => setTier(e.target.value)}
            required
            style={{
              padding: "12px 16px",
              borderRadius: 8,
              border: "1.5px solid #ccc",
              fontSize: 16,
              outline: "none",
              backgroundColor: "#fff",
            }}
          >
            <option value="free">Free</option>
            <option value="creative">Creative</option>
            <option value="dealer">Dealer</option>
            <option value="all-rounder">All-Rounder</option>
          </select>
          {error && (
            <p style={{ color: "red", fontSize: 14, margin: 0, textAlign: "center" }}>{error}</p>
          )}
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
            Sign Up
          </button>
        </form>
        <p style={{ marginTop: 24, fontSize: 14, color: "#444" }}>
          Already have an account?{" "}
          <Link to="/" style={{ color: "#1a73e8", textDecoration: "none" }}>
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}

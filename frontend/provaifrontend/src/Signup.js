// src/Signup.js
import React, { useState, useEffect } from "react";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { auth, db } from "./firebase";
import { useNavigate, Link } from "react-router-dom";
import { doc, setDoc } from "firebase/firestore";
import { useAuthState } from "react-firebase-hooks/auth";
import { serverTimestamp } from "firebase/firestore";

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
        expiry = new Date(now.setFullYear(now.getFullYear() + 100)); // 100 years from now
      } else {
        expiry = new Date(now.setFullYear(now.getFullYear() + 1)); // 1 year from now
      }

      await new Promise((resolve) => {
        const unsubscribe = auth.onAuthStateChanged(async (authUser) => {
          if (authUser && authUser.uid === uid) {
            await setDoc(doc(db, "users", uid), {
              email,
              tier,
              displayName,
              profilePicURL: "", // optionally update later
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

  if (loading) return <div>Loading...</div>;

  return (
    <>
      <h2>Sign Up</h2>
      <form onSubmit={handleSignup}>
        <input
          type="text"
          value={displayName}
          placeholder="Display Name"
          onChange={(e) => setDisplayName(e.target.value)}
          required
        />
        <input
          type="email"
          value={email}
          placeholder="Email"
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          value={password}
          placeholder="Password"
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <select value={tier} onChange={(e) => setTier(e.target.value)} required>
          <option value="free">Free</option>
          <option value="creative">Creative</option>
          <option value="dealer">Dealer</option>
          <option value="all-rounder">All-Rounder</option>
        </select>
        <button type="submit">Sign Up</button>
        {error && <p style={{ color: "red" }}>{error}</p>}
      </form>
      <p style={{ marginTop: "1em" }}>
        Already have an account? <Link to="/">Login</Link>
      </p>
    </>
  );
}

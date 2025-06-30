// src/Login.js
import React, { useState, useEffect } from "react";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "./firebase";
import { Link, useNavigate } from "react-router-dom";
import { useAuthState } from "react-firebase-hooks/auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  const [user, loading] = useAuthState(auth);
  const navigate = useNavigate();

  // Redirect logged-in users away from login page
  useEffect(() => {
    if (user) {
      navigate("/chat");
    }
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

  if (loading) return <div>Loading...</div>;

  return (
    <>
      <form onSubmit={handleLogin}>
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
        <button type="submit">Login</button>
        {error && <p style={{ color: "red" }}>{error}</p>}
      </form>

      <p style={{ marginTop: "1em" }}>
        Forgot password? <Link to="/reset-password">Reset it here</Link>
      </p>
    </>
  );
}

import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "./firebase";
import { useAuthState } from "react-firebase-hooks/auth";
import "./Login.css";

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
    return <div className="login-loading">Loading...</div>;

  return (
    <div className="login-container">
      <div className="login-background"></div>

      <div className="login-center-stack">
        {/* 🟦 Login Form */}
        <div className="login-card">
          <img
            src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
            alt="Logo"
            className="login-logo"
          />
          <h1 className="login-title">Sign in</h1>
          <p className="login-subtitle">Use your account</p>

          <form className="login-form" onSubmit={handleLogin}>
            <input
              type="email"
              value={email}
              placeholder="Email"
              onChange={(e) => setEmail(e.target.value)}
              required
              className="login-input"
            />
            <input
              type="password"
              value={password}
              placeholder="Password"
              onChange={(e) => setPassword(e.target.value)}
              required
              className="login-input"
            />
            {error && <p className="login-error">{error}</p>}
            <div className="login-forgot">
              <Link to="/reset-password">Forgot password?</Link>
            </div>
            <button type="submit" className="login-button">
              Next
            </button>
          </form>

          <p className="login-signup">
            Don't have an account? <Link to="/signup">Sign up here</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

import React, { useState } from "react";
import { sendPasswordResetEmail } from "firebase/auth";
import { auth } from "./firebase";
import { Link } from "react-router-dom";
import "./PasswordReset.css";

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
    <div className="password-reset-container">
      <div className="password-reset-background"></div>

      <div className="password-reset-center-stack">
        <div className="password-reset-card">
          <img
            src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
            alt="Logo"
            className="password-reset-logo"
          />
          <h1 className="password-reset-title">Reset password</h1>
          <p className="password-reset-subtitle">
            Enter your email to reset your password
          </p>

          <form className="password-reset-form" onSubmit={handleReset}>
            <input
              type="email"
              value={email}
              placeholder="Enter your email"
              onChange={(e) => setEmail(e.target.value)}
              required
              className="password-reset-input"
            />
            <button type="submit" className="password-reset-button">
              Send Reset Email
            </button>
            {message && <p className="password-reset-message">{message}</p>}
            {error && <p className="password-reset-error">{error}</p>}
          </form>

          <p className="password-reset-login">
            Back to{" "}
            <Link to="/">Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

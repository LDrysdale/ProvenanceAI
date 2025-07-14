// frontend/provaifrontend/src/TopOfPage.js
import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from "firebase/auth";
import { auth } from "./firebase";
import "./Chat.css";
import logo from "./logo.svg";
import AuthButton from "./AuthButton";

export default function TopOfPage() {
  const [user, setUser] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();
  const path = location.pathname;
  const activeNav = path === "/" ? "home" : path.replace("/", "");

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
    });
    return () => unsubscribe();
  }, []);

  const handleLogin = async () => {
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
    } catch (err) {
      console.error("Login failed:", err);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <>
      <nav className="nav-quarter-circle" aria-label="Main navigation">
        <button
          className={`nav-circle-btn ${activeNav === "home" ? "active-nav-icon" : ""}`}
          style={{ "--i": 0 }}
          title="Home"
          onClick={() => navigate("/home")}
        >
          🏠
        </button>
        <button
          className={`nav-circle-btn ${activeNav === "chat" ? "active-nav-icon" : ""}`}
          style={{ "--i": 1 }}
          title="Chat"
          onClick={() => navigate("/chat")}
        >
          💬
        </button>
        <button
          className={`nav-circle-btn ${activeNav === "settings" ? "active-nav-icon" : ""}`}
          style={{ "--i": 2 }}
          title="Settings"
          onClick={() => navigate("/settings")}
        >
          ⚙️
        </button>
        <button
          className={`nav-circle-btn ${activeNav === "help" ? "active-nav-icon" : ""}`}
          style={{ "--i": 3 }}
          title="Help"
          onClick={() => navigate("/help")}
        >
          ❓
        </button>
      </nav>

      <header className="chat-header">
        <div className="logo-circle">
          <img src={logo} alt="Logo" />
        </div>
        Chat Timeline Interface
        <AuthButton
          isLoggedIn={!!user}
          handleLogin={handleLogin}
          handleLogout={handleLogout}
        />
      </header>
    </>
  );
}

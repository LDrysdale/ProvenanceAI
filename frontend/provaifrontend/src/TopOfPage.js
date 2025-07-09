// src/TopOfPage.js
import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { auth } from "./firebase";
import { signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged } from "firebase/auth";
import { FaSignInAlt, FaSignOutAlt } from "react-icons/fa";
import logo from "./logo.svg";

export default function TopOfPage({ title = "Chat Timeline Interface" }) {
  const navigate = useNavigate();
  const location = useLocation();

  const [user, setUser] = useState(null);

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

  const path = location.pathname;
  const activeNav = path === "/" ? "chat" : path.replace("/", "");

  return (
    <>
      <nav className="nav-quarter-circle" aria-label="Main navigation">
        <button
          className={`nav-circle-btn ${activeNav === "home" ? "active-nav-icon" : ""}`}
          style={{ '--i': 0 }}
          title="Home"
          onClick={() => navigate("/home")}
        >
          🏠
        </button>
        <button
          className={`nav-circle-btn ${activeNav === "chat" ? "active-nav-icon" : ""}`}
          style={{ '--i': 1 }}
          title="Chat"
          onClick={() => navigate("/chat")}
        >
          💬
        </button>
        <button
          className={`nav-circle-btn ${activeNav === "settings" ? "active-nav-icon" : ""}`}
          style={{ '--i': 2 }}
          title="Settings"
          onClick={() => navigate("/settings")}
        >
          ⚙️
        </button>
        <button
          className={`nav-circle-btn ${activeNav === "help" ? "active-nav-icon" : ""}`}
          style={{ '--i': 3 }}
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
        {title}

        <div
          className="auth-icon"
          onClick={user ? handleLogout : handleLogin}
          title={user ? "Logout" : "Login"}
          style={{ position: "absolute", right: "1rem", top: "1rem", cursor: "pointer" }}
        >
          {user ? <FaSignOutAlt size={20} /> : <FaSignInAlt size={20} />}
        </div>
      </header>
    </>
  );
}

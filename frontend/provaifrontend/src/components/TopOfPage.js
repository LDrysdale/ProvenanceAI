import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from "firebase/auth";
import { auth } from "../firebase";
import "./TopOfPage.css";
import logo from "../logo.svg";
import AuthButton from "../AuthButton";

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
    <header className="top-header">
      <div className="top-header__left" onClick={() => navigate("/home")}>
        <img src={logo} alt="Logo" className="top-header__logo" />
        <span className="top-header__title">CerebralAI</span>
      </div>
          <nav className="top-header__nav" aria-label="Main navigation">
        <button
          className={`top-header__nav-btn${activeNav === "home" ? " active" : ""}`}
          title="Home"
          onClick={() => navigate("/home")}
        >
          🏠 <span className="nav-label">Home</span>
        </button>
        <button
          className={`top-header__nav-btn${activeNav === "chat" ? " active" : ""}`}
          title="Chat"
          onClick={() => navigate("/chat")}
        >
          💬 <span className="nav-label">Chat</span>
        </button>
        <button
          className={`top-header__nav-btn${activeNav === "settings" ? " active" : ""}`}
          title="Settings"
          onClick={() => navigate("/settings")}
        >
          ⚙️ <span className="nav-label">Settings</span>
        </button>
        <button
          className={`top-header__nav-btn${activeNav === "help" ? " active" : ""}`}
          title="Help"
          onClick={() => navigate("/help")}
        >
          ❓ <span className="nav-label">Help</span>
        </button>
      </nav>
      <div className="top-header__auth">
        <AuthButton
          isLoggedIn={!!user}
          handleLogin={handleLogin}
          handleLogout={handleLogout}
        />
      </div>
    </header>
  );
}
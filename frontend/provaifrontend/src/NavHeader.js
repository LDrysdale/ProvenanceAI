// src/NavHeader.js
import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import logo from "./logo.svg";

export default function NavHeader() {
  const navigate = useNavigate();
  const location = useLocation();

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
        Chat Timeline Interface
      </header>
    </>
  );
}

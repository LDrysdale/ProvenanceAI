// src/AuthButton.js
import React from "react";
import { FaSignInAlt, FaSignOutAlt } from "react-icons/fa";

export default function AuthButton({ isLoggedIn, handleLogin, handleLogout }) {
  return (
    <div
      className="auth-icon"
      onClick={isLoggedIn ? handleLogout : handleLogin}
      title={isLoggedIn ? "Logout" : "Login"}
      style={{ cursor: "pointer" }}
    >
      {isLoggedIn ? <FaSignOutAlt size={20} /> : <FaSignInAlt size={20} />}
    </div>
  );
}

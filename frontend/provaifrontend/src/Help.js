// src/Help.js
import React, { useState, useEffect } from "react";
import TopOfPage from "./TopOfPage";
import { auth } from "./firebase";
import { signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged } from "firebase/auth";

export default function Help() {
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

  return (
    <div className="chat-app">
      <TopOfPage
        title="Frequently Asked Questions"
        isLoggedIn={!!user}
        handleLogin={handleLogin}
        handleLogout={handleLogout}
      />

      <main className="help-container" style={{ padding: "2rem" }}>
        <h2>FAQ</h2>
        <ul>
          <li><strong>Q:</strong> How do I log in?<br /><strong>A:</strong> Click the icon in the top right corner and sign in with Google.</li>
          <li><strong>Q:</strong> What is this app for?<br /><strong>A:</strong> It helps you visualize and manage your chat timelines.</li>
          <li><strong>Q:</strong> Where are my settings?<br /><strong>A:</strong> Click the ⚙️ icon to access your settings.</li>
          <li><strong>Q:</strong> How do I log out?<br /><strong>A:</strong> Click the logout icon in the top right corner.</li>
        </ul>
        {/* Add more questions as needed */}
      </main>
    </div>
  );
}

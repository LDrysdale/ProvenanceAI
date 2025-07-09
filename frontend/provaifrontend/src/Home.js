// src/Home.js
import React, { useState, useEffect } from "react";
import TopOfPage from "./TopOfPage";
import { auth } from "./firebase";
import {
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
} from "firebase/auth";

export default function Home() {
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
        title="Welcome Home"
        isLoggedIn={!!user}
        handleLogin={handleLogin}
        handleLogout={handleLogout}
      />

      <main className="home-container" style={{ padding: "2rem" }}>
        <h2>Hello {user?.displayName || "Guest"} 👋</h2>
        <p>
          Welcome to your dashboard. Use the navigation to explore chat
          timelines, update settings, or get help.
        </p>
        {!user && (
          <p>
            <strong>Please sign in</strong> to access full features of the
            application.
          </p>
        )}
      </main>
    </div>
  );
}

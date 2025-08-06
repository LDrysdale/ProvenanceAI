import React, { useState, useEffect } from "react";
import TopOfPage from "./components/TopOfPage";
import { auth } from "./firebase";
import { signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged } from "firebase/auth";
import "./Settings.css"; // Ensure you import the styles for .settings-document
import "./Help.css";

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

        <main className="settings-page">
          <div className="settings-document">
            <h2>Frequently Asked Questions</h2>
            <div className="faq-list">
              <div className="faq-item">
                <div className="faq-question">How do I log in?</div>
                <div className="faq-answer">Click the icon in the top right corner and sign in with Google.</div>
              </div>
              <div className="faq-item">
                <div className="faq-question">What is this app for?</div>
                <div className="faq-answer">It helps you visualize and manage your chat timelines.</div>
              </div>
              <div className="faq-item">
                <div className="faq-question">Where are my settings?</div>
                <div className="faq-answer">Click the ⚙️ icon to access your settings.</div>
              </div>
              <div className="faq-item">
                <div className="faq-question">How do I log out?</div>
                <div className="faq-answer">Click the logout icon in the top right corner.</div>
              </div>
              {/* Add more questions as needed */}
            </div>
          </div>
        </main>
    </div>
  );
}
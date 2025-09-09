import React, { useState, useEffect } from "react";
import TopOfPage from "./components/TopOfPage";
import { auth } from "./firebase";
import { signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged } from "firebase/auth";
import "./Settings.css";
import "./Help.css";

// Import FAQ data
import faqs from "./faqs.json";

export default function Help() {
  const [user, setUser] = useState(null);
  const [openIndex, setOpenIndex] = useState(null);

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

  const toggleQuestion = (index) => {
    setOpenIndex(openIndex === index ? null : index);
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
            {faqs.map((faq, index) => (
              <div key={index} className="faq-item">
                <div
                  className="faq-question"
                  onClick={() => toggleQuestion(index)}
                >
                  {faq.question}
                </div>
                <div className={`faq-answer ${openIndex === index ? "open" : ""}`}>
                  {faq.answer}
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

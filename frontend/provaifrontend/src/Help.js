import React, { useState, useEffect } from "react";
import TopOfPage from "./components/TopOfPage";
import { auth } from "./firebase";
import { signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged } from "firebase/auth";
import "./Settings.css";
import "./Help.css";

export default function Help() {
  const [user, setUser] = useState(null);
  const [openIndex, setOpenIndex] = useState(null); // Track which FAQ is open

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
    setOpenIndex(openIndex === index ? null : index); // collapse if open, open if closed
  };

  const faqs = [
    {
      question: "What is the purpose of CerebralAI?",
      answer:
        "This app is designed to be an AI coach/mentor where you can interact with your personal AI assistant to build your very own business/side-hustle from nothing. Take notes, track your progress over time and CerebralAI will match your passion to generate new ideas and turn those ideas into a fully fledged business plan that turns your passion into a moneymaker.",
    },
    {
      question: "How is this site structured?",
      answer: `Think of CerebralAI as having 3 different distinct sections.
1. You have the main chat screen where you can go backwards and forwards with AI.
2. You have the Ideaboard, which can be accessed via the Home page, where you can brainstorm and organize your thoughts.
3. You have the Diary page, which can be accessed via the Home page, where you can add your thoughts/ideas into a plan that will help turn your idea into your business/side-hustle.

From the chat section, you can update both the Ideaboard and the Diary making it a more seamless experience. The more information you put into the Diary or Ideaboard, the more the ideas will relate to you and the better the outcomes will be.`,
    },
    {
      question: "How do I use the main Chat page?",
      answer: `The main Chat page is where you interact with your AI assistant. You have the main navigation bar at the top of the page where you can access other pages of this site including the Home page. The middle of the page is where the questions and answers are displayed. 
Each question(q) and answer(a) pairing start on the left with the next q-a pairing appearing further and further right. Click-and-drag has been enabled when the q-a pairings go beyond the right edge of the screen.

Below the q-a pairings section there is a toolbar section split into 3 parts:
- Left: select "agents" to assist you.
- Middle: prompt input box with + for new chat and send button.
- Right: future features coming.

Below the toolbar is chat history. Click on the pill-shaped boxes to restore a chat.`,
    },
    {
      question: "Where are my settings?",
      answer: "Click the ⚙️ icon to access your settings.",
    },
    {
      question: "How do I log out?",
      answer: "Click the logout icon in the top right corner.",
    },
  ];

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
                <div
                  className={`faq-answer ${openIndex === index ? "open" : ""}`}
                >
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

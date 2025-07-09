// src/Settings.js
import React from "react";
import TopOfPage from "./TopOfPage";

export default function Settings() {
  return (
    <div className="chat-app">
      <TopOfPage title="Settings" />

      <main className="settings-container" style={{ padding: "2rem" }}>
        <h2>Settings Page</h2>
        <p>This is where you'll configure app preferences.</p>
        {/* Add settings form or options here later */}
      </main>
    </div>
  );
}

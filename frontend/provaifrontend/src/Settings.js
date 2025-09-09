import React from "react";
import TopOfPage from "./components/TopOfPage";
import "./Settings.css";

import UserProfile from "./components/UserProfile";
import NotificationSettings from "./components/NotificationSettings";
import ChangePassword from "./components/ChangePassword";
import AccountManagement from "./components/AccountManagement";

export default function Settings() {
  return (
    <div className="chat-app">
      <TopOfPage title="Settings" />

      <main className="settings-page">
        <h2 className="settings-title">⚙️ Settings</h2>

        <div className="settings-section">
          <UserProfile />
        </div>

        <div className="settings-section">
          <NotificationSettings />
        </div>

        <div className="settings-section">
          <ChangePassword />
        </div>

        <div className="settings-section danger">
          <AccountManagement />
        </div>
      </main>
    </div>
  );
}

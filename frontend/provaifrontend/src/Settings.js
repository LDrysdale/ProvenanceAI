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
        <div className="settings-document">
          <h2>Settings</h2>
          <UserProfile />
          <hr />
          <NotificationSettings />
          <hr />
          <ChangePassword />
          <hr />
          <AccountManagement />
        </div>
      </main>
    </div>
  );
}

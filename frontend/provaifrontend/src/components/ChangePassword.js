import React, { useState } from "react";
import { auth } from "../firebase";
import {
  reauthenticateWithCredential,
  EmailAuthProvider,
  updatePassword,
} from "firebase/auth";

export default function ChangePassword() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [status, setStatus] = useState("");

  const handleChange = async () => {
    const user = auth.currentUser;
    const credential = EmailAuthProvider.credential(
      user.email,
      currentPassword
    );

    try {
      await reauthenticateWithCredential(user, credential);
      await updatePassword(user, newPassword);
      setStatus("Password updated successfully.");
    } catch (err) {
      console.error(err);
      setStatus("Failed to change password. Check current password.");
    }
  };

  return (
    <section>
      <h3>Change Password</h3>

      <div
        className="password-row"
        style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", marginBottom: "1rem" }}
      >
        <label style={{ display: "flex", flexDirection: "column" }}>
          Current Password:
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            style={{ marginTop: "0.5rem", padding: "0.5rem", borderRadius: "6px", border: "1px solid #ccc" }}
          />
        </label>

        <label style={{ display: "flex", flexDirection: "column" }}>
          New Password:
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            style={{ marginTop: "0.5rem", padding: "0.5rem", borderRadius: "6px", border: "1px solid #ccc" }}
          />
        </label>
      </div>

      <button
        onClick={handleChange}
        style={{
          marginTop: "1rem",
          padding: "0.6rem 1.2rem",
          backgroundColor: "#0078d4",
          color: "white",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
        }}
      >
        Update Password
      </button>

      <p style={{ marginTop: "0.5rem", color: "#555" }}>{status}</p>
    </section>
  );
}

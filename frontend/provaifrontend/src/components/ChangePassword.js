// components/ChangePassword.js
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
        <div className="password-row">
        <label>
            Current Password:
            <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            />
        </label>
        <label>
            New Password:
            <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            />
        </label>
        </div>
      <button onClick={handleChange}>Update Password</button>
      <p>{status}</p>
    </section>
  );
}

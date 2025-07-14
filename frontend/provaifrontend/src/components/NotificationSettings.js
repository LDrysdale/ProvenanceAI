// components/NotificationSettings.js
import React, { useEffect, useState } from "react";
import { auth, db } from "../firebase";
import { doc, updateDoc, getDoc } from "firebase/firestore";

export default function NotificationSettings() {
  const [emailNotifications, setEmailNotifications] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    const loadSettings = async () => {
      const docRef = doc(db, "users", auth.currentUser.uid);
      const docSnap = await getDoc(docRef);
      if (docSnap.exists()) {
        setEmailNotifications(docSnap.data().emailNotifications ?? false);
      }
    };
    loadSettings();
  }, []);

  const handleToggle = async () => {
    const newValue = !emailNotifications;
    setEmailNotifications(newValue);
    try {
      await updateDoc(doc(db, "users", auth.currentUser.uid), {
        emailNotifications: newValue,
      });
      setStatus("Preferences saved.");
    } catch (err) {
      console.error(err);
      setStatus("Failed to update.");
    }
  };

  return (
    <section>
      <h3>Notification Settings</h3>
      <label>
        <input
          type="checkbox"
          checked={emailNotifications}
          onChange={handleToggle}
        />
        Enable Email Notifications
      </label>
      <p>{status}</p>
    </section>
  );
}

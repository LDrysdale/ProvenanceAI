// components/UserProfile.js
import React, { useEffect, useState } from "react";
import { auth, db } from "../firebase";
import { updateProfile } from "firebase/auth";
import { doc, updateDoc, getDoc } from "firebase/firestore";

export default function UserProfile() {
  const user = auth.currentUser;
  const [displayName, setDisplayName] = useState(user?.displayName || "");
  const [newName, setNewName] = useState(displayName);
  const [status, setStatus] = useState("");

  useEffect(() => {
    const loadUser = async () => {
      const docRef = doc(db, "users", user.uid);
      const docSnap = await getDoc(docRef);
      if (docSnap.exists()) {
        setDisplayName(docSnap.data().displayName || user.displayName);
      }
    };
    loadUser();
  }, [user]);

  const handleUpdate = async () => {
    try {
      await updateProfile(user, { displayName: newName });
      await updateDoc(doc(db, "users", user.uid), {
        displayName: newName,
      });
      setDisplayName(newName);
      setStatus("Display name updated!");
    } catch (err) {
      console.error(err);
      setStatus("Error updating name.");
    }
  };

  return (
    <section>
      <h3>User Profile</h3>
      <p><strong>Email:</strong> {user.email}</p>
      <label>
        <strong>Display Name:</strong>
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          style={{ marginLeft: "1rem" }}
        />
      </label>
      <button onClick={handleUpdate} style={{ marginLeft: "1rem" }}>
        Update
      </button>
      <p>{status}</p>
    </section>
  );
}

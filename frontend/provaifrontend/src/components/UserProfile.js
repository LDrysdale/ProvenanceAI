import React, { useEffect, useState } from "react";
import { auth, db } from "../firebase";
import { updateProfile } from "firebase/auth";
import { doc, updateDoc, getDoc } from "firebase/firestore";

export default function UserProfile() {
  const user = auth.currentUser;
  const [userData, setUserData] = useState(null);
  const [newName, setNewName] = useState(user?.displayName || "");
  const [status, setStatus] = useState("");

  useEffect(() => {
    const loadUser = async () => {
      if (!user) return;
      try {
        const docRef = doc(db, "users", user.uid);
        const docSnap = await getDoc(docRef);

        if (docSnap.exists()) {
          const data = docSnap.data();
          setUserData({
            displayName: data.displayName || user.displayName || "",
            tierName: data.tierName || "Free",
            addons: data.addons || [],
            email: user.email,
          });
          setNewName(data.displayName || user.displayName || "");
        } else {
          // fallback if no user doc
          setUserData({
            displayName: user.displayName || "",
            tierName: "Free",
            addons: [],
            email: user.email,
          });
        }
      } catch (err) {
        console.error("Error loading user:", err);
      }
    };

    loadUser();
  }, [user]);

  const handleUpdate = async () => {
    if (!user) return;
    try {
      await updateProfile(user, { displayName: newName });
      await updateDoc(doc(db, "users", user.uid), {
        displayName: newName,
      });

      setUserData((prev) => ({ ...prev, displayName: newName }));
      setStatus("Display name updated!");
    } catch (err) {
      console.error(err);
      setStatus("Error updating name.");
    }
  };

  if (!userData) {
    return <p>Loading user info...</p>;
  }

  return (
    <section>
      <h3>User Profile</h3>
      <p><strong>Display Name:</strong> {userData.displayName || "Not set"}</p>
      <p><strong>Email:</strong> {userData.email}</p>
      <p><strong>Tier:</strong> {userData.tierName}</p>
      <p>
        <strong>Add-ons:</strong>{" "}
        {userData.addons.length > 0 ? userData.addons.join(", ") : "None"}
      </p>

      <label>
        <strong>Change Display Name:</strong>
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          style={{
            marginLeft: "1rem", 
            marginTop: "0.5rem",
            padding: "0.5rem",
            borderRadius: "6px",
            border: "1px solid #ccc",
          }}
        />
      </label>
      <button
        onClick={handleUpdate}
        style={{
          marginLeft: "0.75rem",
          marginTop: "1rem",
          padding: "0.6rem 1.2rem",
          backgroundColor: "#0078d4",
          color: "white",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
        }}  
      >
        Update
      </button>
      <p>{status}</p>
    </section>
  );
}

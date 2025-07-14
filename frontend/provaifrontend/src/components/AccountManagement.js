// components/AccountManagement.js
import React, { useState } from "react";
import { auth, db } from "../firebase";
import { doc, updateDoc } from "firebase/firestore";

export default function AccountManagement() {
  const [confirm, setConfirm] = useState(false);
  const [status, setStatus] = useState("");

  const handleRequestDelete = async () => {
    const user = auth.currentUser;

    // Example: 30 days from now — adjust logic to match billing cycle
    const deleteAfter = new Date();
    deleteAfter.setDate(deleteAfter.getDate() + 30);

    try {
      await updateDoc(doc(db, "users", user.uid), {
        deleteRequested: true,
        deleteAfter: deleteAfter.toISOString(),
      });
      setStatus("Account deletion scheduled after your plan ends.");
    } catch (err) {
      console.error(err);
      setStatus("Failed to schedule deletion.");
    }
  };

  return (
    <section>
      <h3>Account Management</h3>
      <p>
        You can request account deletion. It will be scheduled to occur after
        your current plan ends.
      </p>
      {confirm ? (
        <button onClick={handleRequestDelete}>Confirm Delete Request</button>
      ) : (
        <button onClick={() => setConfirm(true)}>Request Account Deletion</button>
      )}
      <p>{status}</p>
    </section>
  );
}

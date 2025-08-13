import React from "react";
import { getAuth } from "firebase/auth";

function GetTokenPage() {
  const auth = getAuth();

  const handleGetToken = async () => {
    const user = auth.currentUser;
    if (!user) {
      alert("No user logged in!");
      return;
    }
    const token = await user.getIdToken();
    console.log("Firebase ID Token:", token);
    alert("Token logged to console.");
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Get Firebase Auth Token</h2>
      <button onClick={handleGetToken}>Get Token</button>
    </div>
  );
}

export default GetTokenPage;

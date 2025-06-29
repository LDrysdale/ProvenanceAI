import React, { useEffect, useRef, useState } from "react";
import { initializeApp } from "firebase/app";
import { getAuth, onAuthStateChanged, GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import * as firebaseui from "firebaseui";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// Firebase configuration (if you want to keep it for later use)
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_AUTH_DOMAIN",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_STORAGE_BUCKET",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const USE_LOCAL_DATA = 1; // Set to 1 to use mock data, 0 to use Firebase

const mockUsers = [
  { email: "test@example.com", password: "password123", firstName: "John", tier: "Gold" },
  // Add more mock users here as needed
];

export default function FirebaseAuthLogin() {
  const navigate = useNavigate();
  const uiRef = useRef(null);
  const uiInstanceRef = useRef(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    console.log("USE_LOCAL_DATA:", USE_LOCAL_DATA);

    if (USE_LOCAL_DATA) {
      console.log("Rendering Mock Login Form");
      // Mock login logic
      return;
    }

    console.log("Initializing Firebase Authentication");
    // Firebase authentication logic
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      console.log("User state changed:", user);
      if (user) {
        user.getIdToken().then((idToken) => {
          axios
            .post("YOUR_BACKEND_LOGIN_URL", { token: idToken })
            .then((response) => {
              console.log("Login successful", response.data);
              navigate("/app");  // Redirect to the app after successful login
            })
            .catch((error) => {
              console.error("Error during backend authentication", error);
            });
        });
      }
    });

    if (!uiInstanceRef.current) {
      uiInstanceRef.current = new firebaseui.auth.AuthUI(auth);
    }

    const uiConfig = {
      signInSuccessUrl: "/app",  // Redirect after login
      signInOptions: [
        auth.EmailAuthProvider.PROVIDER_ID,
        GoogleAuthProvider.PROVIDER_ID,
      ],
      callbacks: {
        signInSuccessWithAuthResult: () => false,  // Prevent automatic redirect by FirebaseUI
      },
    };

    if (uiRef.current) {
      uiInstanceRef.current.start(uiRef.current, uiConfig);
    }

    return () => unsubscribe();
  }, [navigate]);

  // Handle mock login
  const handleMockLogin = () => {
    console.log("Attempting Mock Login");
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    // Simulate mock login check
    const user = mockUsers.find((u) => u.email === email && u.password === password);

    if (user) {
      // Mock successful login
      setLoading(true);
      setTimeout(() => {
        console.log(`Mock Login successful for ${user.firstName} (${user.tier})`);
        navigate("/app"); // Redirect to app after mock login
      }, 500);
    } else {
      alert("Invalid email or password");
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "auto", padding: "2rem" }}>
      <h2>Login Page</h2>
      {USE_LOCAL_DATA ? (
        <div>
          <input type="email" id="email" placeholder="Email" />
          <input type="password" id="password" placeholder="Password" />
          <button onClick={handleMockLogin}>Login with Mock Data</button>
        </div>
      ) : (
        <div>
          <h3>Login with Firebase</h3>
          <div ref={uiRef}></div>
        </div>
      )}
    </div>
  );
}

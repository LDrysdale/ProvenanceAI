import React, { useEffect, useRef, useState } from "react";
import { initializeApp } from "firebase/app";
import { getAuth, onAuthStateChanged, GoogleAuthProvider } from "firebase/auth";
import * as firebaseui from "firebaseui";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// Firebase configuration
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

  // Use useEffect to ensure FirebaseUI is initialized once the DOM is ready
  useEffect(() => {
    if (USE_LOCAL_DATA) {
      console.log("Rendering Mock Login Form");
      return; // If using mock data, no need to initialize FirebaseUI
    }

    console.log("Initializing Firebase Authentication");

    // Listen for auth state changes
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

    // Initialize Firebase UI when the DOM is ready
    const initializeUI = () => {
      if (uiRef.current && !uiInstanceRef.current) {
        uiInstanceRef.current = new firebaseui.auth.AuthUI(auth);

        const uiConfig = {
          signInSuccessUrl: "/app",  // Redirect after login
          signInOptions: [
            GoogleAuthProvider.PROVIDER_ID,  // Add more sign-in methods if needed
            auth.EmailAuthProvider.PROVIDER_ID,
          ],
          callbacks: {
            signInSuccessWithAuthResult: () => false, // Prevent automatic redirect by FirebaseUI
          },
        };

        // Initialize Firebase UI only if the UI element is available
        uiInstanceRef.current.start(uiRef.current, uiConfig);
      }
    };

    // Only initialize Firebase UI after the component is mounted and `uiRef` is available
    setTimeout(() => {
      initializeUI();
    }, 100); // Small delay to allow DOM to initialize before calling Firebase UI

    return () => {
      unsubscribe();
    };
  }, [navigate]);

  const handleMockLogin = () => {
    console.log("Attempting Mock Login");
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const user = mockUsers.find((u) => u.email === email && u.password === password);

    if (user) {
      setLoading(true);
      setTimeout(() => {
        console.log(`Mock Login successful for ${user.firstName} (${user.tier})`);
        navigate("/app");
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
          <div ref={uiRef}></div> {/* Firebase UI will render inside this div */}
        </div>
      )}
    </div>
  );
}

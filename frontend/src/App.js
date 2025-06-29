import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import FirebaseAuthLogin from "./FirebaseAuthLogin";  // Firebase login
import MockUserLogin from "./MockUserLogin";  // Mock login
import ProvenanceMain from "./ProvenanceMain";  // Main AI tool page

import { getAuth, onAuthStateChanged } from "firebase/auth";

function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const auth = getAuth();
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  if (loading) return <div>Loading...</div>;

  if (!user) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default function App() {
  // Hardcode the USE_LOCAL_DATA flag
  const USE_LOCAL_DATA = 1;  // Set to 1 to use mock data, 0 to use Firebase

  return (
    <BrowserRouter>
      <Routes>
        {/* Check USE_LOCAL_DATA flag */}
        <Route
          path="/"
          element={USE_LOCAL_DATA === 1 ? <MockUserLogin /> : <FirebaseAuthLogin />}
        />
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <ProvenanceMain />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

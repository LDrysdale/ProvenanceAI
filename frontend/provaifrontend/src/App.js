import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthState } from "react-firebase-hooks/auth";
import { auth } from "./firebase";

import Login from "./Login";
import Signup from "./Signup";
import Chat from "./Chat";
import PasswordReset from "./PasswordReset";
import Settings from "./Settings";
import Home from "./Home";
import Help from "./Help";

function ProtectedRoute({ children }) {
  const [user, loading] = useAuthState(auth);

  if (loading) return <div>Loading...</div>;

  if (!user) return <Navigate to="/" replace />;

  return children;
}

export default function App() {
  const [user, loading] = useAuthState(auth);

  if (loading) return <div>Loading...</div>;

  return (
    <BrowserRouter>
      <Routes>
        {/* If logged in, redirect "/" to "/chat". Otherwise show Login */}
        <Route path="/" element={user ? <Navigate to="/chat" replace /> : <Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/reset-password" element={<PasswordReset />} />

        <Route path="/home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        <Route path="/help" element={<ProtectedRoute><Help /></ProtectedRoute>} />

        {/* Catch-all redirects */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

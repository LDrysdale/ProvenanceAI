// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDa_mfwBPtZz5yd85g1JqeCF_u0vFfpq_o",
  authDomain: "provenanceai-firebase.firebaseapp.com",
  projectId: "provenanceai-firebase",
  storageBucket: "provenanceai-firebase.firebasestorage.app",
  messagingSenderId: "1019874913698",
  appId: "1:1019874913698:web:30403efd7c1f39d13cd6fb"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

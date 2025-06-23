import React from "react";
import ReactDOM from "react-dom/client";
import ChatWithImagePrompt from "./App";
import "./styles.css"; // Optional: if you want to add Tailwind or custom CSS

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <ChatWithImagePrompt />
  </React.StrictMode>
);

const express = require("express");
const cors = require("cors");
const path = require("path");
const fs = require("fs");

const app = express();
const port = 8000;

// Enable CORS for local testing
app.use(cors());
app.use(express.json());

// Path to mock user JSON file
const mockUserFilePath = path.join(__dirname, "..", "tests", "datasets", "mock_user.json");

// Load mock user data once on server start
let mockUsers = [];
try {
  const fileData = fs.readFileSync(mockUserFilePath, "utf-8");
  mockUsers = JSON.parse(fileData);
  console.log(`Loaded ${mockUsers.length} mock users`);
} catch (err) {
  console.error("Error loading mock user data:", err);
}

// POST /api/auth/mock_login
// Accepts JSON: { first_name: string, last_name: string }
app.post("/api/auth/mock_login", (req, res) => {
  const { first_name, last_name } = req.body;

  if (!first_name || !last_name) {
    return res.status(400).json({ error: "Missing first_name or last_name" });
  }

  // Check if user exists in mock user list (case-insensitive)
  const user = mockUsers.find(
    (u) =>
      u.first_name.toLowerCase() === first_name.toLowerCase() &&
      u.last_name.toLowerCase() === last_name.toLowerCase()
  );

  if (!user) {
    return res.status(401).json({ error: "Invalid user credentials" });
  }

  // Return mock token (for simplicity)
  const mockToken = `mock-token-for-${user.first_name.toLowerCase()}-${user.last_name.toLowerCase()}`;

  res.json({
    token: mockToken,
    user: {
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email || null,
    },
  });
});

// Start server
app.listen(port, () => {
  console.log(`Mock auth backend running on http://localhost:${port}`);
});

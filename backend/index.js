const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const admin = require("firebase-admin");

const app = express();
const port = process.env.PORT || 4000;

app.use(cors());
app.use(bodyParser.json());

// Use environment variable to switch mock mode
const useLocalData = process.env.USE_LOCAL_DATA === "1";

// Firebase Admin setup (only if not in mock mode)
if (!useLocalData) {
  const serviceAccount = require("./serviceAccountKey.json");

  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
  });
}

// Middleware to authenticate requests
async function authenticate(req, res, next) {
  if (useLocalData) {
    // Check mock token
    const authHeader = req.headers.authorization || "";
    if (authHeader !== "Bearer mocktoken123") {
      return res.status(401).json({ error: "Unauthorized (mock)" });
    }
    return next();
  } else {
    // Verify Firebase ID token
    const authHeader = req.headers.authorization || "";
    if (!authHeader.startsWith("Bearer ")) {
      return res.status(401).json({ error: "Unauthorized" });
    }
    const idToken = authHeader.split("Bearer ")[1];
    try {
      const decodedToken = await admin.auth().verifyIdToken(idToken);
      req.user = decodedToken;
      next();
    } catch (e) {
      return res.status(401).json({ error: "Unauthorized: invalid token" });
    }
  }
}

app.post("/ask", authenticate, (req, res) => {
  const { message } = req.body;
  if (!message) {
    return res.status(400).json({ error: "Missing 'message' in request body" });
  }

  // Fake AI response
  const responseText = `AI Response to your prompt: "${message}"`;

  res.json({ response: responseText });
});

app.listen(port, () => {
  console.log(`Backend listening on port ${port}`);
});

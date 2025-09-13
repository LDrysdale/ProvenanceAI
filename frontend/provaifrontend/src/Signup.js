import React, { useState, useEffect } from "react";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { auth, db } from "./firebase";
import { useNavigate, Link } from "react-router-dom";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";
import { useAuthState } from "react-firebase-hooks/auth";
import "./Signup.css";

// Stripe
import { loadStripe } from "@stripe/stripe-js";

const stripePromise = loadStripe("YOUR_STRIPE_PUBLISHABLE_KEY");

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tier, setTier] = useState("free");
  const [addons, setAddons] = useState([]);
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState(null);

  const [user, loading] = useAuthState(auth);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate("/chat");
  }, [user, navigate]);

  const handleSignup = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const uid = userCredential.user.uid;
      const now = new Date();
      const expiry = tier === "free"
        ? new Date(now.setFullYear(now.getFullYear() + 100))
        : new Date(now.setFullYear(now.getFullYear() + 1));

      await new Promise((resolve) => {
        const unsubscribe = auth.onAuthStateChanged(async (authUser) => {
          if (authUser && authUser.uid === uid) {
            await setDoc(doc(db, "users", uid), {
              email,
              tier,
              addons,
              displayName,
              profilePicURL: "",
              subscriptionStatus: tier === "free" ? "lifetime" : "active",
              membershipExpiry: expiry.toISOString(),
              createdAt: serverTimestamp(),
            });
            unsubscribe();
            resolve();
          }
        });
      });

      navigate("/chat");
    } catch (err) {
      console.error("🔥 Error during signup or Firestore write:", err);
      setError(err.message);
    }
  };

  if (loading) return <div style={{ textAlign: "center", marginTop: 40 }}>Loading...</div>;

  const features = [
    { name: "Ideas Generator", free: true, paid: true },
    { name: "Momentum Manager", free: false, paid: true },
    { name: "Business Plan Generator", free: false, paid: true },
    { name: "Psychologist Tool", free: false, paid: true },
    { name: "Adaptor Coach", free: false, paid: true },
  ];

  const availableAddons = [
    { name: "Psychologist", desc: "Access AI psychologist", price: 15 },
    { name: "No Limits", desc: "Remove all usage limits", price: 25 },
  ];

  const tierPricing = { free: 0, paid: 49 };

  const toggleAddon = (name) => {
    setAddons((prev) =>
      prev.includes(name) ? prev.filter((a) => a !== name) : [...prev, name]
    );
  };

  const addonsTotal = addons.reduce(
    (acc, a) => acc + (availableAddons.find((add) => add.name === a)?.price || 0),
    0
  );

  const totalCost = tierPricing[tier] + addonsTotal;

  const handleStripeCheckout = async () => {
    const stripe = await stripePromise;
    const response = await fetch("/create-checkout-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tier, addons }),
    });
    const session = await response.json();
    const result = await stripe.redirectToCheckout({ sessionId: session.id });
    if (result.error) console.error(result.error.message);
  };

  return (
    <div className="signup-container">
      <div className="signup-background"></div>

      <div className="signup-center-stack two-column-layout">
        {/* Left column: signup form */}
        <div className="signup-card left-column">
          <img
            src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
            alt="Logo"
            className="signup-logo"
          />
          <h1>Create account</h1>

          <form onSubmit={handleSignup} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <input type="text" placeholder="Display Name" value={displayName} onChange={e => setDisplayName(e.target.value)} className="signup-input" required />
            <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} className="signup-input" required />
            <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="signup-input" required />
            {error && <p className="signup-error">{error}</p>}
            <button type="submit" className="signup-button">Sign Up</button>
          </form>

          <p className="signup-login">
            Already have an account? <Link to="/">Login</Link>
          </p>
        </div>

        {/* Right column: features + addons grid */}
        <div className="right-column">
          {/* Features table */}
          <div className="tier-card-container">
            <table className="tier-table">
              <thead>
                <tr>
                  <th>Features</th>
                  {["free", "paid"].map(t => (
                    <th key={t} onClick={() => setTier(t)} className="tier-header">
                      <div className={`tier-pill ${tier === t ? "selected" : ""}`}>
                        {t === "free" ? "Free" : "Paid"}
                        <div className="tier-price">{t === "free" ? "$0" : "$49 / 3 months"}</div>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {features.map(f => (
                  <tr key={f.name}>
                    <td className="feature-name">{f.name}</td>
                    <td>{f.free ? <span className="tick">✔</span> : <span className="cross">✖</span>}</td>
                    <td>{f.paid ? <span className="tick">✔</span> : <span className="cross">✖</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Addons + Totals + Checkout 2x2 grid */}
          <div className="addons-grid">
            {/* Row 1 */}
            <div className={`addon-card ${addons.includes("Psychologist") ? "selected" : ""}`} onClick={() => toggleAddon("Psychologist")}>
              <div className="addon-title">Psychologist</div>
              <div className="addon-desc">Access AI psychologist</div>
              <div className="addon-price">$15</div>
            </div>

            <div className={`addon-card ${addons.includes("No Limits") ? "selected" : ""}`} onClick={() => toggleAddon("No Limits")}>
              <div className="addon-title">No Limits</div>
              <div className="addon-desc">Remove all usage limits</div>
              <div className="addon-price">$25</div>
            </div>

            {/* Row 2 */}
            <div className="addon-card total-cost-card">
              <h3>Total Cost</h3>
              <p>${totalCost}</p>
            </div>

            <div
              className="addon-card checkout-card"
              onClick={handleStripeCheckout}
              style={{ cursor: "pointer" }}
            >
              <div className="addon-title">Checkout</div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect, useCallback } from "react";

const TIERS = ["free", "creative", "dealer", "all-rounder"];

export default function MembershipManager({ userId }) {
  const [currentTier, setCurrentTier] = useState("");
  const [expiryDate, setExpiryDate] = useState(null);
  const [selectedTier, setSelectedTier] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // Fetch current membership info wrapped in useCallback for stable reference
  const fetchMembership = useCallback(async () => {
    try {
      const res = await fetch("/api/user/membership", {
        headers: { "X-User-Id": userId },
      });
      if (!res.ok) throw new Error("Failed to fetch membership");
      const data = await res.json();
      setCurrentTier(data.tier);
      setExpiryDate(data.membershipExpiry);
      setSelectedTier(data.tier);
    } catch (err) {
      setMessage("Error fetching membership info.");
      console.error(err);
    }
  }, [userId]);

  useEffect(() => {
    fetchMembership();
  }, [fetchMembership]);

  // Handler for upgrading/changing membership
  const handleUpgrade = async () => {
    if (selectedTier === currentTier) {
      setMessage("You are already on this tier.");
      return;
    }
    const confirmed = window.confirm(
      `Are you sure you want to change your membership from "${currentTier}" to "${selectedTier}"?`
    );
    if (!confirmed) return;

    setLoading(true);
    setMessage("");

    try {
      const res = await fetch("/membership/update", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": userId,
        },
        body: JSON.stringify({ user_id: userId, new_tier: selectedTier }),
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to update membership");
      }
      setMessage("Membership update started successfully.");

      // Poll updated membership every 2 seconds, max 5 attempts
      let attempts = 0;
      const pollInterval = setInterval(async () => {
        attempts++;
        try {
          const statusRes = await fetch("/api/user/membership", {
            headers: { "X-User-Id": userId },
          });
          const statusData = await statusRes.json();
          if (statusData.tier === selectedTier) {
            setCurrentTier(selectedTier);
            setExpiryDate(statusData.membershipExpiry);
            setMessage("Membership updated successfully!");
            clearInterval(pollInterval);
            setLoading(false);
          } else if (attempts >= 5) {
            setMessage("Membership update pending, please refresh later.");
            clearInterval(pollInterval);
            setLoading(false);
          }
        } catch (err) {
          console.error("Polling error:", err);
          clearInterval(pollInterval);
          setLoading(false);
        }
      }, 2000);
    } catch (err) {
      setMessage(err.message);
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "auto", padding: 20 }}>
      <h2>Your Membership</h2>
      <p>
        <strong>Current Tier:</strong> {currentTier || "Loading..."}
      </p>
      <p>
        <strong>Expiry Date:</strong>{" "}
        {expiryDate ? new Date(expiryDate).toLocaleDateString() : "Loading..."}
      </p>

      <label htmlFor="tier-select">Change Membership Tier:</label>
      <select
        id="tier-select"
        value={selectedTier}
        onChange={(e) => setSelectedTier(e.target.value)}
        disabled={loading}
        style={{ width: "100%", marginBottom: 10 }}
      >
        {TIERS.map((tier) => (
          <option
            key={tier}
            value={tier}
            disabled={tier === currentTier}
          >
            {tier.charAt(0).toUpperCase() + tier.slice(1)}
          </option>
        ))}
      </select>

      <button
        onClick={handleUpgrade}
        disabled={loading || selectedTier === currentTier}
        style={{ width: "100%", padding: "10px", fontSize: "1rem" }}
      >
        {loading ? "Updating..." : "Update Membership"}
      </button>

      {message && (
        <p
          style={{
            marginTop: 10,
            color: message.toLowerCase().includes("error") ? "red" : "green",
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
}

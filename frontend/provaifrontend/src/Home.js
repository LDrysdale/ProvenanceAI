import React, { useState, useEffect, useRef } from "react";
import TopOfPage from "./TopOfPage";
import { getAuth, GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signOut } from "firebase/auth";
import { UserCircle, CalendarDays, Lightbulb } from "lucide-react";
import "./Home.css";

const auth = getAuth();

export default function Home() {
  const [user, setUser] = useState(null);
  const [diaryEntries, setDiaryEntries] = useState({});
  const [entryText, setEntryText] = useState("");
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
    });
    return () => unsubscribe();
  }, []);

  const handleLogin = async () => {
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
    } catch (err) {
      console.error("Login failed:", err);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  const addEntry = () => {
    if (entryText.trim()) {
      const newEntries = {
        ...diaryEntries,
        [selectedDate]: [
          { text: entryText, timestamp: new Date().toISOString() },
          ...(diaryEntries[selectedDate] || [])
        ]
      };
      setDiaryEntries(newEntries);
      setEntryText("");
    }
  };

  const deleteEntry = (index) => {
    const updatedEntries = [...(diaryEntries[selectedDate] || [])];
    updatedEntries.splice(index, 1);
    setDiaryEntries({ ...diaryEntries, [selectedDate]: updatedEntries });
  };

  const isToday = selectedDate === new Date().toISOString().split("T")[0];

  // Drag-scroll state & refs
  const diaryRef = useRef(null);
  const isDragging = useRef(false);
  const startY = useRef(0);
  const scrollTop = useRef(0);

  // Mouse handlers
  const handleMouseDown = (e) => {
    isDragging.current = true;
    startY.current = e.clientY;
    scrollTop.current = diaryRef.current.scrollTop;
    // Prevent text selection while dragging
    diaryRef.current.style.userSelect = "none";
  };

  const handleMouseMove = (e) => {
    if (!isDragging.current) return;
    const dy = e.clientY - startY.current;
    diaryRef.current.scrollTop = scrollTop.current - dy;
  };

  const handleMouseUp = () => {
    isDragging.current = false;
    diaryRef.current.style.userSelect = "auto";
  };

  // Touch handlers for mobile
  const handleTouchStart = (e) => {
    isDragging.current = true;
    startY.current = e.touches[0].clientY;
    scrollTop.current = diaryRef.current.scrollTop;
    diaryRef.current.style.userSelect = "none";
  };

  const handleTouchMove = (e) => {
    if (!isDragging.current) return;
    const dy = e.touches[0].clientY - startY.current;
    diaryRef.current.scrollTop = scrollTop.current - dy;
  };

  const handleTouchEnd = () => {
    isDragging.current = false;
    diaryRef.current.style.userSelect = "auto";
  };

  return (
    <div className="home-container">
      <TopOfPage />

      <div className="dashboard-grid">
        {/* Top-Left: User Profile */}
        <div className="card profile-card">
          <div className="card-header">
            <UserCircle className="icon" />
            <h2>User Profile</h2>
          </div>
          {user ? (
            <>
              <p><strong>Name:</strong> {user.displayName}</p>
              <p><strong>Email:</strong> {user.email}</p>
              <button className="logout-button" onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <>
              <p>You’re not logged in.</p>
              <button className="login-button" onClick={handleLogin}>Login with Google</button>
            </>
          )}
        </div>

        {/* Bottom-Left: IdeaBoard Preview */}
        <div className="card ideaboard-card">
          <div className="card-header">
            <Lightbulb className="icon" />
            <h2>IdeaBoard Preview</h2>
          </div>
          <p>Preview coming soon...</p>
        </div>

        {/* Right Side: Diary (spanning both rows) */}
        <div
          className="card diary-card"
          ref={diaryRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          <div className="card-header">
            <CalendarDays className="icon" />
            <h2>Diary</h2>
          </div>

          <div className="date-selector">
            <strong>{isToday ? "Today" : selectedDate}</strong>
            {isToday && <span>({new Date().toLocaleDateString()})</span>}
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
          </div>

          <div className="diary-entry-input">
            <textarea
              placeholder="Write your entry..."
              value={entryText}
              onChange={(e) => setEntryText(e.target.value)}
              rows={3}
              maxLength={500}
            />

            <button onClick={addEntry}>Add</button>
          </div>

          <div className="diary-entries">
            {(diaryEntries[selectedDate] || []).length === 0 ? (
              <p className="no-entries">No entries for this day.</p>
            ) : (
              diaryEntries[selectedDate].map((entry, index) => (
                <div className="diary-entry" key={index}>
                  <div>
                    <p className="entry-text">{entry.text}</p>
                    <p className="entry-date">
                      {new Date(entry.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <button onClick={() => deleteEntry(index)} className="delete-button">
                    Delete
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

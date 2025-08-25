import React, { useState, useRef, useEffect } from "react";
import TopOfPage from "./components/TopOfPage";
import "./DiaryPage.css";
import useDragAndDrop from "./components/clickanddrag";
import { Eye, EyeOff } from "lucide-react";

export default function DiaryPage({ diaryEntries: initialEntries }) {
  const containerRef = useRef(null);

  const [diaryEntries, setDiaryEntries] = useState(initialEntries || {});
  const [months, setMonths] = useState(() => {
    const current = new Date();
    return [
      new Date(current.getFullYear(), current.getMonth() - 1, 1),
      current,
      new Date(current.getFullYear(), current.getMonth() + 1, 1),
    ];
  });

  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [entryText, setEntryText] = useState("");

  // Morph modal
  const [focusedDate, setFocusedDate] = useState(null);

  useDragAndDrop(containerRef);

  const getWeeksForMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDayOfMonth = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const daysArray = [
      ...Array(firstDayOfMonth).fill(null),
      ...Array(daysInMonth).fill().map((_, i) => i + 1),
    ];

    const weeks = [];
    for (let i = 0; i < daysArray.length; i += 7) {
      weeks.push(daysArray.slice(i, i + 7));
    }
    return weeks;
  };

  // Infinite scroll
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const monthHeight = el.clientHeight;

    const handleScroll = () => {
      const scrollTop = el.scrollTop;

      if (scrollTop < monthHeight / 2) {
        setMonths((prev) => {
          const firstMonth = prev[0];
          const prevMonth = new Date(
            firstMonth.getFullYear(),
            firstMonth.getMonth() - 1,
            1
          );
          return [prevMonth, ...prev];
        });
        el.scrollTop += monthHeight;
      }

      if (scrollTop > (months.length - 1) * monthHeight - monthHeight / 2) {
        setMonths((prev) => {
          const lastMonth = prev[prev.length - 1];
          const nextMonth = new Date(
            lastMonth.getFullYear(),
            lastMonth.getMonth() + 1,
            1
          );
          return [...prev, nextMonth];
        });
      }
    };

    el.addEventListener("scroll", handleScroll);
    return () => el.removeEventListener("scroll", handleScroll);
  }, [months]);

  const handleAddEntry = () => {
    if (!entryText.trim()) return;

    setDiaryEntries((prev) => {
      const entriesForDate = prev[selectedDate] || [];
      return {
        ...prev,
        [selectedDate]: [
          ...entriesForDate,
          { text: entryText, timestamp: new Date().toISOString() },
        ],
      };
    });
    setEntryText("");
  };

  const handleDeleteEntry = (date, index) => {
    setDiaryEntries((prev) => {
      const updatedEntries = [...prev[date]];
      updatedEntries.splice(index, 1);
      return {
        ...prev,
        [date]: updatedEntries.length ? updatedEntries : undefined,
      };
    });
  };

  const toggleFocusDate = (date) => {
    setFocusedDate(focusedDate === date ? null : date);
  };

  return (
    <div className="diarypage-container">
      <TopOfPage />

      <div className="diary-main-layout">
        {/* Left panel */}
        <div className="diary-entry-panel">
          <h3>Manage Entries</h3>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
          <textarea
            placeholder="Write your entry..."
            value={entryText}
            onChange={(e) => setEntryText(e.target.value)}
            rows={5}
          />
          <button onClick={handleAddEntry}>Add Entry</button>
        </div>

        {/* Scrollable months */}
        <div ref={containerRef} className="months-outer">
          {months.map((monthDate) => {
            const weeks = getWeeksForMonth(monthDate);
            const year = monthDate.getFullYear();
            const month = monthDate.getMonth();

            return (
              <div key={monthDate.toISOString()} className="month-card">
                <h3 className="month-label">
                  {monthDate.toLocaleString("default", {
                    month: "long",
                    year: "numeric",
                  })}
                </h3>

                <div className="weekdays-row">
                  {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map(
                    (day) => (
                      <div key={day} className="weekday-label">
                        {day}
                      </div>
                    )
                  )}
                </div>

                <div className="weeks-container">
                  {weeks.map((week, weekIndex) => (
                    <div className="week-row" key={weekIndex}>
                      {week.map((day, dayIndex) => {
                        if (day === null)
                          return (
                            <div
                              key={dayIndex}
                              className="card calendar-day empty"
                            ></div>
                          );

                        const dateKey = new Date(
                          year,
                          month,
                          day
                        ).toISOString().split("T")[0];
                        const entries = diaryEntries?.[dateKey] || [];

                        return (
                          <div className="card calendar-day" key={dayIndex}>
                            <div className="calendar-day-header">
                              {day}
                              {entries.length > 0 && (
                                <button
                                  className="focus-btn"
                                  onClick={() => toggleFocusDate(dateKey)}
                                >
                                  {focusedDate === dateKey ? (
                                    <EyeOff size={16} />
                                  ) : (
                                    <Eye size={16} />
                                  )}
                                </button>
                              )}
                            </div>

                            <div className="calendar-entries">
                              {entries.length === 0 ? (
                                <p className="no-entries">No entries</p>
                              ) : (
                                entries.map((entry, idx) => (
                                  <div className="diary-entry" key={idx}>
                                    <div className="entry-text">
                                      {entry.text.length > 15
                                        ? entry.text.slice(0, 15) + "..."
                                        : entry.text}
                                    </div>
                                    <div className="entry-date">
                                      {new Date(entry.timestamp).toLocaleTimeString()}
                                    </div>
                                    <button
                                      onClick={() => handleDeleteEntry(dateKey, idx)}
                                    >
                                      Delete
                                    </button>
                                  </div>
                                ))
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Morph modal for full entries */}
      {focusedDate && (
        <div
          className="entry-morph-overlay"
          onClick={() => setFocusedDate(null)}
        >
          <div
            className="entry-morph-container"
            onClick={(e) => e.stopPropagation()}
          >
            <h3>
            {new Date(focusedDate).toLocaleDateString("default", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric"
            })}
            </h3>
            {diaryEntries[focusedDate].map((entry, idx) => (
              <div className="diary-entry" key={idx}>
                <p className="entry-text">{entry.text}</p>
                <p className="entry-date">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </p>
                <button onClick={() => handleDeleteEntry(focusedDate, idx)}>
                  Delete
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

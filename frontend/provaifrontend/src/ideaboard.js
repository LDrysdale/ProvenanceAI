import React, { useState, useRef, useEffect } from "react";
import Draggable from "react-draggable";
import { Trash2, CornerDownRight } from "lucide-react";
import TopOfPage from "./components/TopOfPage";
import "./IdeaBoard.css";

const NOTE_WIDTH = 150;
const NOTE_HEIGHT = 100;

// Word-based similarity (0..1)
function calculateSimilarity(textA = "", textB = "") {
  const norm = (s) =>
    String(s)
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .split(/\s+/)
      .filter(Boolean);

  const A = norm(textA);
  const B = norm(textB);
  if (A.length === 0 || B.length === 0) return 0;

  const bSet = new Set(B);
  const common = A.filter((w) => bSet.has(w));
  const avgLen = (A.length + B.length) / 2;
  return Math.min(1, common.length / Math.max(1, avgLen));
}

export default function IdeaBoard() {
  const boardRef = useRef(null);
  const noteRefs = useRef({});
  const [notes, setNotes] = useState([
    { id: Date.now() + 1, title: "AI Idea", content: "Train model on diary entries", x: 100, y: 100, width: NOTE_WIDTH, height: NOTE_HEIGHT },
    { id: Date.now() + 2, title: "Frontend", content: "Add draggable notes UI", x: 360, y: 160, width: NOTE_WIDTH, height: NOTE_HEIGHT },
  ]);
  const [noteToDelete, setNoteToDelete] = useState(null);
  const [editing, setEditing] = useState({ noteId: null, field: null });
  const [notePositions, setNotePositions] = useState({});

  useEffect(() => {
    const positions = {};
    notes.forEach((note) => {
      const el = noteRefs.current[note.id];
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const boardRect = boardRef.current.getBoundingClientRect();
      positions[note.id] = {
        x: rect.left + rect.width / 2 - boardRect.left,
        y: rect.top + rect.height / 2 - boardRect.top,
      };
    });
    setNotePositions(positions);
  }, [notes]);

  const similarityMatrix = notes.map((a) =>
    notes.map((b) => (a.id === b.id ? 0 : calculateSimilarity(a.content, b.content)))
  );

  const addNote = () => {
    const boardRect = boardRef.current?.getBoundingClientRect();
    const maxW = boardRect ? Math.max(200, boardRect.width - NOTE_WIDTH - 40) : window.innerWidth - NOTE_WIDTH - 40;
    const maxH = boardRect ? Math.max(200, boardRect.height - NOTE_HEIGHT - 100) : window.innerHeight - NOTE_HEIGHT - 140;
    const randomX = Math.floor(Math.random() * maxW) + 20;
    const randomY = Math.floor(Math.random() * maxH) + 20;
    setNotes((prev) => [...prev, { id: Date.now(), title: `Idea ${prev.length + 1}`, content: "New thought...", x: randomX, y: randomY, width: NOTE_WIDTH, height: NOTE_HEIGHT }]);
  };

  const handleDrag = (e, data, id) => {
    setNotes((prev) => prev.map((n) => (n.id === id ? { ...n, x: data.x, y: data.y } : n)));
  };

  const confirmDelete = (id) => setNoteToDelete(id);
  const deleteNote = () => { setNotes((prev) => prev.filter((n) => n.id !== noteToDelete)); setNoteToDelete(null); };
  const cancelDelete = () => setNoteToDelete(null);

  const startEditing = (noteId, field) => setEditing({ noteId, field });
  const stopEditing = () => setEditing({ noteId: null, field: null });
  const handleChange = (noteId, field, value) => setNotes((prev) => prev.map((n) => (n.id === noteId ? { ...n, [field]: value } : n)));

  const startResizing = (e, noteId) => {
    e.stopPropagation();
    const startX = e.clientX;
    const startY = e.clientY;
    const note = notes.find((n) => n.id === noteId);
    const startWidth = note.width;
    const startHeight = note.height;

    const onMouseMove = (e) => {
      const newWidth = Math.max(80, startWidth + (e.clientX - startX));
      const newHeight = Math.max(60, startHeight + (e.clientY - startY));
      setNotes((prev) => prev.map((n) => (n.id === noteId ? { ...n, width: newWidth, height: newHeight } : n)));
    };
    const onMouseUp = () => { window.removeEventListener("mousemove", onMouseMove); window.removeEventListener("mouseup", onMouseUp); };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  };

  const getLineColor = (sim) => {
    const startColor = [173, 216, 230]; // lightblue
    const endColor = [0, 0, 255]; // dark blue
    const r = startColor[0] + (endColor[0] - startColor[0]) * sim;
    const g = startColor[1] + (endColor[1] - startColor[1]) * sim;
    const b = startColor[2] + (endColor[2] - startColor[2]) * sim;
    return `rgb(${r},${g},${b})`;
  };

  return (
    <div className="idea-board-wrapper">
      <TopOfPage title="IdeaBoard" />
      <div className="add-note-bar">
        <button className="add-note-button" onClick={addNote}>+ Add Note</button>
      </div>
      <div className="idea-board-container" ref={boardRef}>
        {/* Connection Lines */}
        <svg className="connection-layer">
          {notes.map((a, i) =>
            notes.map((b, j) => {
              if (i >= j) return null;
              const sim = similarityMatrix[i][j] || 0;
              if (sim === 0) return null;
              const posA = notePositions[a.id];
              const posB = notePositions[b.id];
              if (!posA || !posB) return null;
              const strokeWidth = 1 + sim * 6;
              const strokeOpacity = 0.25 + sim * 0.75;
              const midX = (posA.x + posB.x) / 2;
              const midY = (posA.y + posB.y) / 2;
              return (
                <g key={`${a.id}-${b.id}`}>
                  <line
                    x1={posA.x} y1={posA.y} x2={posB.x} y2={posB.y}
                    stroke={getLineColor(sim)}
                    strokeWidth={strokeWidth}
                    strokeOpacity={strokeOpacity}
                    vectorEffect="non-scaling-stroke"
                    strokeLinecap="round"
                  />
                  <rect
                    x={midX - 15}
                    y={midY - 10}
                    width={30}
                    height={16}
                    fill="white"
                    opacity={0.7}
                    rx={3}
                  />
                  <text
                    x={midX} y={midY + 3}
                    fontSize="12"
                    fontWeight="bold"
                    fill="black"
                    textAnchor="middle"
                    alignmentBaseline="middle"
                  >
                    {(sim * 100).toFixed(0)}%
                  </text>
                </g>
              );
            })
          )}
        </svg>

        {/* Notes */}
        {notes.map((note) => (
          <Draggable key={note.id} position={{ x: note.x, y: note.y }} onDrag={(e, data) => handleDrag(e, data, note.id)}>
            <div className="note" ref={(el) => (noteRefs.current[note.id] = el)} style={{ width: note.width, height: note.height }}>
              <button className="delete-btn" onMouseDown={(e) => e.stopPropagation()} onClick={() => confirmDelete(note.id)}>
                <Trash2 size={16} />
              </button>
              <div className="note-body">
                {editing.noteId === note.id && editing.field === "title" ? (
                  <input
                    className="note-title-input"
                    value={note.title}
                    onChange={(e) => handleChange(note.id, "title", e.target.value)}
                    onBlur={stopEditing}
                    onKeyDown={(e) => e.key === "Enter" && stopEditing()}
                    autoFocus
                  />
                ) : (
                  <h4 onDoubleClick={() => startEditing(note.id, "title")}>{note.title}</h4>
                )}
                {editing.noteId === note.id && editing.field === "content" ? (
                  <textarea
                    className="note-content-input"
                    value={note.content}
                    onChange={(e) => handleChange(note.id, "content", e.target.value)}
                    onBlur={stopEditing}
                    autoFocus
                  />
                ) : (
                  <p onDoubleClick={() => startEditing(note.id, "content")}>{note.content}</p>
                )}
              </div>
              {/* Resize icon */}
              <CornerDownRight
                className="resize-icon"
                size={16}
                onMouseDown={(e) => startResizing(e, note.id)}
              />
            </div>
          </Draggable>
        ))}

        {/* Delete Confirmation */}
        {noteToDelete !== null && (
          <div className="modal-overlay">
            <div className="modal">
              <p>Are you sure you want to delete this note?</p>
              <div className="modal-actions">
                <button className="confirm-btn" onClick={deleteNote}>Yes</button>
                <button className="cancel-btn" onClick={cancelDelete}>Cancel</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

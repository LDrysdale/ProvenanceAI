import React, { useEffect, useRef } from "react";

export default function DotCluster() {
  const canvasRef = useRef(null);
  const dotsRef = useRef([]);
  const targetRef = useRef(null);
  const clickingRef = useRef(false);

  // Store random active clicks as an array of {x, y, expirationTime}
  const randomClicksRef = useRef([]);

  useEffect(() => {
    const setupDots = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const spacing = 30; // Adjust spacing as needed

      const bufferX = width * 4;
      const bufferY = height * 4;

      const cols = Math.floor((width + bufferX * 2) / spacing);
      const rows = Math.floor((height + bufferY * 2) / spacing);

      const newDots = [];
      for (let y = 0; y <= rows; y++) {
        for (let x = 0; x <= cols; x++) {
          const posX = x * spacing - bufferX;
          const posY = y * spacing - bufferY;
          newDots.push({
            originalX: posX,
            originalY: posY,
            currentX: posX,
            currentY: posY,
            vx: 0,
            vy: 0,
          });
        }
      }
      dotsRef.current = newDots;
    };

    setupDots();
    window.addEventListener("resize", setupDots);
    return () => window.removeEventListener("resize", setupDots);
  }, []);

  useEffect(() => {
    const handleMouseDown = (e) => {
      clickingRef.current = true;
      targetRef.current = { x: e.clientX, y: e.clientY };
    };
    const handleMouseMove = (e) => {
      if (clickingRef.current) {
        targetRef.current = { x: e.clientX, y: e.clientY };
      }
    };
    const handleMouseUp = () => {
      clickingRef.current = false;
      targetRef.current = null;
    };

    window.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  // New: create random clicks every few seconds that last 5 seconds each
  useEffect(() => {
    const addRandomClick = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const x = Math.random() * width;
      const y = Math.random() * height;
      const expireTime = Date.now() + 5000; // lasts 5 seconds

      randomClicksRef.current.push({ x, y, expireTime });
    };

    // Add a new random click every 1.5 seconds (adjust frequency if desired)
    const intervalId = setInterval(addRandomClick, 1500);

    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const dotRadius = 3;
    const springFactor = 0.07;
    const damping = 0.8;
    const maxMove = 30;

    let bufferX = window.innerWidth * 4;
    let bufferY = window.innerHeight * 4;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      bufferX = window.innerWidth * 4;
      bufferY = window.innerHeight * 4;
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Clean up expired random clicks
      const now = Date.now();
      randomClicksRef.current = randomClicksRef.current.filter(
        (click) => click.expireTime > now
      );

      dotsRef.current.forEach((dot) => {
        // Combine all attraction points:
        // - user click if active
        // - all active random clicks

        let totalDx = 0;
        let totalDy = 0;
        let attractionCount = 0;

        // User click attraction
        if (clickingRef.current && targetRef.current) {
          let dx = targetRef.current.x - dot.currentX;
          let dy = targetRef.current.y - dot.currentY;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist > maxMove) {
            dx = (dx / dist) * maxMove;
            dy = (dy / dist) * maxMove;
          }
          totalDx += dx;
          totalDy += dy;
          attractionCount++;
        }

        // Random clicks attraction
        randomClicksRef.current.forEach(({ x, y }) => {
          let dx = x - dot.currentX;
          let dy = y - dot.currentY;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist > maxMove) {
            dx = (dx / dist) * maxMove;
            dy = (dy / dist) * maxMove;
          }
          totalDx += dx;
          totalDy += dy;
          attractionCount++;
        });

        if (attractionCount > 0) {
          // Average the vector
          totalDx /= attractionCount;
          totalDy /= attractionCount;

          dot.vx = (dot.vx + totalDx * springFactor) * damping;
          dot.vy = (dot.vy + totalDy * springFactor) * damping;

          dot.currentX += dot.vx;
          dot.currentY += dot.vy;
        } else {
          // No active clicks, spring back to original
          const dx = dot.originalX - dot.currentX;
          const dy = dot.originalY - dot.currentY;

          dot.vx = (dot.vx + dx * springFactor) * damping;
          dot.vy = (dot.vy + dy * springFactor) * damping;

          dot.currentX += dot.vx;
          dot.currentY += dot.vy;
        }

        // Wrap horizontally
        if (dot.currentX < -bufferX) {
          dot.currentX += canvas.width + bufferX * 2;
          dot.originalX += canvas.width + bufferX * 2;
        } else if (dot.currentX > canvas.width + bufferX) {
          dot.currentX -= canvas.width + bufferX * 2;
          dot.originalX -= canvas.width + bufferX * 2;
        }

        // Wrap vertically
        if (dot.currentY < -bufferY) {
          dot.currentY += canvas.height + bufferY * 2;
          dot.originalY += canvas.height + bufferY * 2;
        } else if (dot.currentY > canvas.height + bufferY) {
          dot.currentY -= canvas.height + bufferY * 2;
          dot.originalY -= canvas.height + bufferY * 2;
        }

        ctx.beginPath();
        ctx.arc(dot.currentX, dot.currentY, dotRadius, 0, 2 * Math.PI);
        ctx.fillStyle = "rgba(0, 35, 102, 0.25)";
        ctx.fill();
      });

      requestAnimationFrame(animate);
    };

    animate();

    return () => window.removeEventListener("resize", resizeCanvas);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 0,
        pointerEvents: "none",
      }}
    />
  );
}

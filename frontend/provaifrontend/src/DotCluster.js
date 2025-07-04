import React, { useEffect, useRef } from "react";

export default function DotCluster() {
  const canvasRef = useRef(null);
  const dotsRef = useRef([]);
  const attractorsRef = useRef([]);

  useEffect(() => {
    const spacing = 30;
    const bufferMultiplier = 3;
    let bufferX, bufferY, width, height;

    const setupDots = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      bufferX = width * bufferMultiplier;
      bufferY = height * bufferMultiplier;

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
            lastX: posX,
            lastY: posY,
            vx: 0,
            vy: 0,
          });
        }
      }
      dotsRef.current = newDots;
    };

    setupDots();
    window.addEventListener("resize", () => setupDots());
    return () => window.removeEventListener("resize", setupDots);
  }, []);

  // ✅ Each mousedown creates a new attractor with its own timer
  useEffect(() => {
    const handleMouseDown = (e) => {
      attractorsRef.current.push({
        x: e.clientX,
        y: e.clientY,
        startTime: performance.now(),
      });
    };
    window.addEventListener("mousedown", handleMouseDown);
    return () => window.removeEventListener("mousedown", handleMouseDown);
  }, []);

  // Optional: add random attractors every few seconds (unchanged)
  useEffect(() => {
    const interval = setInterval(() => {
      attractorsRef.current.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        startTime: performance.now(),
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    let width = window.innerWidth;
    let height = window.innerHeight;
    let bufferX = width * 3;
    let bufferY = height * 3;

    const dotRadius = 3;
    const springFactor = 0.015;
    const damping = 0.85;
    const maxMove = 25;
    const maxVel = 15;
    const attractorDuration = 2500; // ✅ Each attractor lives for 2.5 seconds

    const resizeCanvas = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
      bufferX = width * 3;
      bufferY = height * 3;
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const timestep = 1000 / 60;
    let lastUpdate = performance.now();
    let accumulator = 0;

    function physicsStep() {
      const now = performance.now();

      // ✅ Remove expired attractors
      attractorsRef.current = attractorsRef.current.filter(
        (a) => now - a.startTime < attractorDuration
      );

      const activeAttractors = attractorsRef.current;

      dotsRef.current.forEach((dot) => {
        dot.lastX = dot.currentX;
        dot.lastY = dot.currentY;

        let vx = dot.vx * damping;
        let vy = dot.vy * damping;

        if (activeAttractors.length > 0) {
          activeAttractors.forEach(({ x, y, startTime }) => {
            const age = now - startTime;
            const progress = 1 - age / attractorDuration;

            let dx = x - dot.currentX;
            let dy = y - dot.currentY;

            const distSq = dx * dx + dy * dy;
            const maxMoveSq = maxMove * maxMove;

            if (distSq > maxMoveSq) {
              const scale = maxMove / Math.sqrt(distSq);
              dx *= scale;
              dy *= scale;
            }

            vx += dx * springFactor * progress;
            vy += dy * springFactor * progress;
          });

          const velSq = vx * vx + vy * vy;
          if (velSq > maxVel * maxVel) {
            const scale = maxVel / Math.sqrt(velSq);
            vx *= scale;
            vy *= scale;
          }

          dot.vx = vx;
          dot.vy = vy;

          dot.currentX += dot.vx;
          dot.currentY += dot.vy;
        } else {
          const dx = dot.originalX - dot.currentX;
          const dy = dot.originalY - dot.currentY;

          dot.vx = (dot.vx + dx * springFactor) * damping;
          dot.vy = (dot.vy + dy * springFactor) * damping;

          dot.currentX += dot.vx;
          dot.currentY += dot.vy;
        }

        // Wrap-around
        if (dot.currentX < -bufferX) {
          dot.currentX += width + bufferX * 2;
          dot.originalX += width + bufferX * 2;
          dot.lastX += width + bufferX * 2;
        } else if (dot.currentX > width + bufferX) {
          dot.currentX -= width + bufferX * 2;
          dot.originalX -= width + bufferX * 2;
          dot.lastX -= width + bufferX * 2;
        }

        if (dot.currentY < -bufferY) {
          dot.currentY += height + bufferY * 2;
          dot.originalY += height + bufferY * 2;
          dot.lastY += height + bufferY * 2;
        } else if (dot.currentY > height + bufferY) {
          dot.currentY -= height + bufferY * 2;
          dot.originalY -= height + bufferY * 2;
          dot.lastY -= height + bufferY * 2;
        }
      });
    }

    let rafId;
    const render = () => {
      const now = performance.now();
      accumulator += now - lastUpdate;
      lastUpdate = now;

      while (accumulator >= timestep) {
        physicsStep();
        accumulator -= timestep;
      }

      const alpha = accumulator / timestep;

      ctx.clearRect(0, 0, width, height);
      dotsRef.current.forEach((dot) => {
        const interpX = dot.lastX + (dot.currentX - dot.lastX) * alpha;
        const interpY = dot.lastY + (dot.currentY - dot.lastY) * alpha;

        ctx.beginPath();
        ctx.arc(interpX, interpY, dotRadius, 0, 2 * Math.PI);
        ctx.fillStyle = "rgba(0, 35, 102, 0.25)";
        ctx.fill();
      });

      rafId = requestAnimationFrame(render);
    };

    lastUpdate = performance.now();
    rafId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      cancelAnimationFrame(rafId);
    };
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

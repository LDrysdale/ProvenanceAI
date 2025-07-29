// frontend/provaifrontend/src/components/clickanddrag.js
import { useEffect } from "react";

export default function useDragAndDrop(scrollRef) {
  useEffect(() => {
    const scrollEl = scrollRef.current;
    if (!scrollEl) return;

    let isDown = false;
    let startX, startY, scrollLeft, scrollTop;
    let velocityX = 0, velocityY = 0;
    let momentumID;
    let lastMoveTime = 0, lastX = 0, lastY = 0;

    const momentumScroll = () => {
      velocityX *= 0.95;
      velocityY *= 0.95;

      if (Math.abs(velocityX) > 0.5 || Math.abs(velocityY) > 0.5) {
        scrollEl.scrollLeft -= velocityX;
        scrollEl.scrollTop -= velocityY;
        momentumID = requestAnimationFrame(momentumScroll);
      } else {
        cancelAnimationFrame(momentumID);
      }
    };

    const handleStart = (pageX, pageY) => {
      isDown = true;
      scrollEl.classList.add("dragging");
      startX = pageX - scrollEl.offsetLeft;
      startY = pageY - scrollEl.offsetTop;
      scrollLeft = scrollEl.scrollLeft;
      scrollTop = scrollEl.scrollTop;
      lastX = pageX;
      lastY = pageY;
      lastMoveTime = Date.now();
      cancelAnimationFrame(momentumID);
      velocityX = 0;
      velocityY = 0;
    };

    const handleMove = (pageX, pageY) => {
      if (!isDown) return;

      const now = Date.now();
      const dt = now - lastMoveTime || 16;

      const dx = pageX - lastX;
      const dy = pageY - lastY;

      velocityX = (dx / dt) * 16;
      velocityY = (dy / dt) * 16;

      lastX = pageX;
      lastY = pageY;
      lastMoveTime = now;

      const x = pageX - scrollEl.offsetLeft;
      const y = pageY - scrollEl.offsetTop;
      const walkX = x - startX;
      const walkY = y - startY;

      scrollEl.scrollLeft = scrollLeft - walkX;
      scrollEl.scrollTop = scrollTop - walkY;
    };

    const handleEnd = () => {
      isDown = false;
      scrollEl.classList.remove("dragging");
      momentumID = requestAnimationFrame(momentumScroll);
    };

    const mouseDown = (e) => {
      e.preventDefault();
      handleStart(e.pageX, e.pageY);
    };
    const mouseMove = (e) => {
      e.preventDefault();
      handleMove(e.pageX, e.pageY);
    };

    const touchStart = (e) => handleStart(e.touches[0].pageX, e.touches[0].pageY);
    const touchMove = (e) => handleMove(e.touches[0].pageX, e.touches[0].pageY);

    scrollEl.addEventListener("mousedown", mouseDown);
    scrollEl.addEventListener("mousemove", mouseMove);
    scrollEl.addEventListener("mouseup", handleEnd);
    scrollEl.addEventListener("mouseleave", handleEnd);
    scrollEl.addEventListener("touchstart", touchStart, { passive: false });
    scrollEl.addEventListener("touchmove", touchMove, { passive: false });
    scrollEl.addEventListener("touchend", handleEnd);

    return () => {
      scrollEl.removeEventListener("mousedown", mouseDown);
      scrollEl.removeEventListener("mousemove", mouseMove);
      scrollEl.removeEventListener("mouseup", handleEnd);
      scrollEl.removeEventListener("mouseleave", handleEnd);
      scrollEl.removeEventListener("touchstart", touchStart);
      scrollEl.removeEventListener("touchmove", touchMove);
      scrollEl.removeEventListener("touchend", handleEnd);
      cancelAnimationFrame(momentumID);
    };
  }, [scrollRef]);
}

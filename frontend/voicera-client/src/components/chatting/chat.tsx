import { useState, useRef } from "react";
import styles from "./chat.module.css";
import Button from "../common/Button";

export default function VoiceraSwipeScreen() {
  const [position, setPosition] = useState(0);
  const [isDragging, setIsDragging] = useState(false);

  const startY = useRef(0);
  const currentY = useRef(0);

  const handleTouchStart = (e) => {
    setIsDragging(true);
    startY.current = e.touches[0].clientY;
    currentY.current = position;
  };

  const handleTouchMove = (e) => {
    if (!isDragging) return;

    const deltaY = e.touches[0].clientY - startY.current;
    const newPosition = Math.max(
      -100,
      Math.min(0, currentY.current + (deltaY / window.innerHeight) * 100)
    );

    setPosition(newPosition);
  };

  const handleTouchEnd = () => {
    setIsDragging(false);
    setPosition(position < -50 ? -100 : 0);
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    startY.current = e.clientY;
    currentY.current = position;
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;

    const deltaY = e.clientY - startY.current;
    const newPosition = Math.max(
      -100,
      Math.min(0, currentY.current + (deltaY / window.innerHeight) * 100)
    );

    setPosition(newPosition);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setPosition(position < -50 ? -100 : 0);
  };

  return (
    <div
      className={styles["voicera-container"]}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => isDragging && handleMouseUp()}
    >
      {/* First Screen */}
      <div
        className={styles["screen-first"]}
        style={{
          transform: `translateY(${position}%)`,
          pointerEvents: position === -100 ? "none" : "auto",
        }}
      >
        <div className={styles["screen-first-content"]}>
          <div className={styles["logo-container"]}>
            <img
              src="/image.png"
              alt="Voicera logo"
              className={styles["logo-icon"]}
            />
          </div>
          <h1 className={styles["title"]}>ASK VOICERA</h1>

        <Button>
          See transcription
        </Button>
        </div>
      </div>
    </div>
  );
}

import React, { useEffect, useState } from "react";
import styles from "./chat.module.css";
import { useSwipeScreen } from "../../hooks/useSwipeScreen";

interface Preferences {
  language: string;
  tone: string;
  agentName: string;
  memoryNotes: string;
}


export default function VoiceraSwipeScreen() {
  const {
    position,
    isDragging,
    isSecondScreenActive,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    openSecondScreen,
    closeSecondScreen,
  } = useSwipeScreen();

  const [language, setLanguage] = useState("English");
  const [tone, setTone] = useState("Friendly");
  const [agentName, setAgentName] = useState("Voicera");
  const [memoryNotes, setMemoryNotes] = useState("");


  const tones = ["Friendly", "Formal", "Casual", "Professional", "Playful"];

  return (
    <div
      className={styles.voiceraContainer}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => isDragging && handleMouseUp()}
      role="application"
      aria-label="Voicera swipe screen"
    >
      <div
        className={styles.screenFirst}
        style={{
          transform: `translateY(${position}%) scale(${isDragging ? 0.97 : 1})`,
          opacity: position <= -95 ? 0 : 1,
          pointerEvents: isSecondScreenActive ? "none" : "auto",
        }}
      >
        <div className={styles.screenFirstContent}>
          <div className={styles.brandRow}>
            <h1 className={styles.title}>Voicera </h1>
          </div>

          <p className={styles.subtitle}>Voice-first assistance for everyone</p>

          <button
            type="button"
            className={styles.primaryButton}
            onClick={openSecondScreen}
          >
            Set your preferences
          </button>

          <div className={styles.swipeHint} aria-hidden="true">
            <span>Swipe up to begin</span>
            <div className={styles.chevron}></div>
          </div>
        </div>
      </div>

      <div
        className={styles.screenSecond}
        style={{
          transform: `translateY(${100 + position}%)`,
          pointerEvents: isSecondScreenActive ? "auto" : "none",
        }}
      >
        <div className={styles.screenSecondContent}>
          <header className={styles.secondHeader}>
            <button
              type="button"
              className={styles.backButton}
              onClick={closeSecondScreen}
              aria-label="Go back"
            >
              ←
            </button>
            <div>
              <h2 className={styles.titleLarge}>Your preferences</h2>
              <p className={styles.secondSubtitle}>
                Tell Voicera how you like to talk and what to remember.
              </p>
            </div>
          </header>

          <form className={styles.prefForm}>
            <div className={styles.fieldGroup}>
              <label className={styles.fieldLabel} htmlFor="language">
                Preferred language
              </label>
              <select
                id="language"
                className={styles.fieldSelect}
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="English">English</option>
                <option value="Spanish">Spanish</option>
                <option value="French">French</option>
                <option value="German">German</option>
                <option value="Portuguese">Portuguese</option>
              </select>
            </div>

            <div className={styles.fieldGroup}>
              <span className={styles.fieldLabel}>Tone of voice</span>
              <div className={styles.tonePills}>
                {tones.map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`${styles.tonePill} ${tone === t ? styles.tonePillActive : ""}`}
                    onClick={() => setTone(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className={styles.fieldGroup}>
              <label className={styles.fieldLabel} htmlFor="agentName">
                Agent name
              </label>
              <input
                id="agentName"
                className={styles.fieldInput}
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
                placeholder="e.g. Nova, Orion, Study Coach"
              />
            </div>

            <div className={styles.fieldGroup}>
              <label className={styles.fieldLabel} htmlFor="memoryNotes">
                Anything specific you want Voicera to remember?
              </label>
              <textarea
                id="memoryNotes"
                className={styles.fieldTextarea}
                rows={4}
                value={memoryNotes}
                onChange={(e) => setMemoryNotes(e.target.value)}
                placeholder="e.g. I prefer concise answers, I’m a backend dev, I’m in PST…"
              />
            </div>

            <div className={styles.buttonRow}>
              <button
                type="button"
                className={`${styles.primaryButton} ${styles.secondaryButton}`}
                onClick={closeSecondScreen}
              >
                Skip for now
              </button>
              <button type="submit" className={styles.primaryButton}>
                Save preferences
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

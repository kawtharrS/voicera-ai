import React, { useState } from "react";
import styles from "./chat.module.css";
import { useSwipeScreen } from "../../hooks/useSwipeScreen";
import api from "../../api/axios";
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tones = ["Friendly", "Formal", "Casual", "Professional", "Playful"];

  const handleSavePreferences = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.post("/save-prefrence", {
        language,
        tone,
        name: agentName,
        preference: memoryNotes,
      });

      closeSecondScreen();
    } catch (err: any) {
      const message =
        err.response?.data?.message ||
        err.message ||
        "Failed to save preferences";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

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
      {/* FIRST SCREEN */}
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
            <h1 className={styles.title}>Voicera</h1>
          </div>

          <p className={styles.subtitle}>
            Voice-first assistance for everyone
          </p>

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

          <form className={styles.prefForm} onSubmit={handleSavePreferences}>
            {/* LANGUAGE */}
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
                <option>English</option>
                <option>Spanish</option>
                <option>French</option>
                <option>German</option>
                <option>Portuguese</option>
              </select>
            </div>

            {/* TONE */}
            <div className={styles.fieldGroup}>
              <span className={styles.fieldLabel}>Tone of voice</span>
              <div className={styles.tonePills}>
                {tones.map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`${styles.tonePill} ${
                      tone === t ? styles.tonePillActive : ""
                    }`}
                    onClick={() => setTone(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {/* AGENT NAME */}
            <div className={styles.fieldGroup}>
              <label className={styles.fieldLabel} htmlFor="agentName">
                Agent name
              </label>
              <input
                id="agentName"
                className={styles.fieldInput}
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
                placeholder="e.g. Nova, Orion"
              />
            </div>

            {/* MEMORY */}
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
                placeholder="I prefer concise answers, I'm a backend dev..."
              />
            </div>

            {error && (
              <p className={styles.errorText} role="alert">
                {error}
              </p>
            )}

            <div className={styles.buttonRow}>
              <button
                type="button"
                className={`${styles.primaryButton} ${styles.secondaryButton}`}
                onClick={closeSecondScreen}
                disabled={loading}
              >
                Skip for now
              </button>

              <button
                type="submit"
                className={styles.primaryButton}
                disabled={loading}
              >
                {loading ? "Saving..." : "Save preferences"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

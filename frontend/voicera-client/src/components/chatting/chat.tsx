import styles from "./chat.module.css";
import { useSwipeScreen } from "../../hooks/useSwipeScreen";
import { useAudioTTS } from "../../hooks/useAudioTTS";
import { useChat } from "../../hooks/useChat";

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

  const { speak } = useAudioTTS(null);

  const { input, setInput, messages, waiting, currentCategory, sendMessage } = useChat(
    (text, category) => speak(text, category)
  );

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const getCategoryColor = (category?: string) => {
    switch (category) {
      case "study":
        return "#4CAF50";
      case "work":
        return "#2196F3";
      case "personal":
        return "#FF9800";
      default:
        return "#999";
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
    >
      <div
        className={styles.screenFirst}
        style={{
          transform: `translateY(${position}%)`,
          opacity: position === -100 ? 0 : 1,
          pointerEvents: isSecondScreenActive ? "none" : "auto",
        }}
      >
        <div className={styles.screenFirstContent}>
          <div className={styles.logoContainer}>
            <img src="/image.png" alt="Voicera logo" className={styles.logoIcon} />
          </div>
          <h1 className={styles.title}>ASK VOICERA</h1>
          <button
            className={styles.transcriptionButton}
            onClick={() => {
              openSecondScreen();
              speak("Start Chat");
            }}
          >
            Start Chat
          </button>
          <p
            style={{ color: "#999", fontSize: "0.875rem", marginTop: "1rem", cursor: "pointer" }}
            onClick={() => speak("Swipe up or tap button to open chat")}
          >
            Swipe up or tap button to open chat
          </p>
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
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
              <button
                onClick={() => {
                  closeSecondScreen();
                  speak("Go back");
                }}
                style={{
                  background: "none",
                  border: "none",
                  color: "white",
                  fontSize: "1.5rem",
                  cursor: "pointer",
                  padding: "0.5rem",
                }}
                aria-label="Go back"
              >
                ←
              </button>
              <h1 className={styles.titleLarge}>Chat with Voicera</h1>
            </div>

            {currentCategory && currentCategory !== "greeting" && (
              <div
                style={{
                  padding: "0.25rem 0.75rem",
                  borderRadius: "12px",
                  backgroundColor: getCategoryColor(currentCategory),
                  color: "white",
                  fontSize: "0.75rem",
                  fontWeight: "600",
                  textTransform: "uppercase",
                  cursor: "pointer",
                }}
                onClick={() => speak(`Current mode: ${currentCategory}`)}
              >
                {currentCategory}
              </div>
            )}
          </div>

          <div className={styles.chatArea}>
            {messages.map((msg: any, i) => (
              <div key={i}>
                <div
                  className={`${styles.chatMessage} ${msg.sender === "user" ? styles.user : styles.ai
                    }`}
                >
                  <span
                    className={styles.chatBubble}
                    tabIndex={0}
                    onClick={() =>
                      speak(msg.sender === "user" ? `You said: ${msg.text}` : `AI says: ${msg.text}`)
                    }
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        speak(
                          msg.sender === "user" ? `You said: ${msg.text}` : `AI says: ${msg.text}`
                        );
                      }
                    }}
                    style={{ cursor: "pointer" }}
                  >
                    {msg.text}
                  </span>
                </div>
              </div>
            ))}
            {waiting && (
              <div className={`${styles.chatMessage} ${styles.ai}`}>
                <div
                  className={styles.typingIndicator}
                  tabIndex={0}
                  onClick={() => speak("AI is typing")}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      speak("AI is typing");
                    }
                  }}
                  style={{ cursor: "pointer" }}
                >
                  <div className={styles.typingDot}></div>
                  <div className={styles.typingDot}></div>
                  <div className={styles.typingDot}></div>
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSend} className={styles.chatForm}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about study, work, or anything..."
              className={styles.chatInput}
              disabled={waiting}
              onClick={() => speak("Type your message")}
            />
            <button
              type="submit"
              className={styles.transcriptionButton}
              disabled={waiting || !input.trim()}
              style={{ flexShrink: 0 }}
              onClick={(e) => {
                if (!waiting && input.trim()) {
                  speak("Send message");
                }
              }}
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
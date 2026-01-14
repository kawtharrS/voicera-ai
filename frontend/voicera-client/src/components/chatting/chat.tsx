import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import styles from "./chat.module.css";
import api from "../../api/axios";

const fetchTTS = async (text: string) => {
  const response = await api.get("/tts", {
    params: { text },
    responseType: "blob",
  });
  if (response.data.size === 0) throw new Error("Empty audio blob received");
  return response.data;
};

export default function VoiceraSwipeScreen() {
  const [position, setPosition] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [input, setInput] = useState("");
  const [waiting, setWaiting] = useState(false);
  const [isSecondScreenActive, setIsSecondScreenActive] = useState(false);
  const [messages, setMessages] = useState([
    { sender: "ai", text: "Hi Ask me anything." },
  ]);
  const [userId, setUserId] = useState<number | null>(null);

  const [userInteracted, setUserInteracted] = useState(false);
  const ttsQueue = useRef<string[]>([]);

  const startY = useRef(0);
  const currentY = useRef(0);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const response = await api.get("/current-user");
        if (response.data.ok && response.data.user) {
          setUserId(response.data.user.id);
          console.log("full user object:", response.data.user);
        }
      } catch (error: unknown) {
        console.error("  - Error:", error);
      }
    };
    fetchCurrentUser();
  }, []);

  const ttsMutation = useMutation({
    mutationFn: fetchTTS,
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onloadeddata = () => console.log("Audio loaded successfully");
      audio.onerror = (e) => console.error("Audio playback error:", e);
      audio.play().then(() => {
        audio.onended = () => {
          URL.revokeObjectURL(url);
        };
      });
    },
    onError: (err) => {
      console.error("TTS error:", err);
    },
  });

  const speak = useCallback(
    (text: string) => {
      if (!text) return;
      if (!userInteracted) {
        ttsQueue.current.push(text);
        return;
      }
      ttsMutation.mutate(text);
    },
    [userInteracted, ttsMutation]
  );

  useEffect(() => {
    const handleFirstClick = () => setUserInteracted(true);
    document.addEventListener("click", handleFirstClick, { once: true });
    return () => document.removeEventListener("click", handleFirstClick);
  }, []);

  useEffect(() => {
    if (userInteracted && ttsQueue.current.length > 0) {
      ttsQueue.current.forEach((text) => speak(text));
      ttsQueue.current = [];
    }
  }, [userInteracted, speak]);

  const handleTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
    setIsDragging(true);
    startY.current = e.touches[0].clientY;
    currentY.current = position;
  };

  const handleTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
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
    const isOpening = position < -30;
    setPosition(isOpening ? -100 : 0);
    setIsSecondScreenActive(isOpening);
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    startY.current = e.clientY;
    currentY.current = position;
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
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
    const isOpening = position < -30;
    setPosition(isOpening ? -100 : 0);
    setIsSecondScreenActive(isOpening);
  };

  const handleSend = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || waiting) return;

    const userMessage = input.trim();

    setMessages((msgs) => [...msgs, { sender: "user", text: userMessage }]);
    setInput("");
    setWaiting(true);

    try {
      const response = await api.post("/ask", { question: userMessage });
      const aiText = response.data.response || "No answer received.";

      setMessages((msgs) => [
        ...msgs,
        {
          sender: "ai",
          text: aiText,
        },
      ]);

      speak(aiText);

      if (userId) {
        try {
          await api.post("/save-memo", {
            user_id: userId,
            user_query: userMessage,
            ai_query: aiText,
          });
        } catch (saveError: unknown) {
          console.error("  - Error:", saveError);
        }
      }
    } catch {
      const errorText = "Sorry, there was an error contacting the server.";
      setMessages((msgs) => [
        ...msgs,
        {
          sender: "ai",
          text: errorText,
        },
      ]);
      speak(errorText);
    } finally {
      setWaiting(false);
    }
  };

  const handleGoBack = () => {
    setPosition(0);
    setIsSecondScreenActive(false);
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
            <img
              src="/image.png"
              alt="Voicera logo"
              className={styles.logoIcon}
            />
          </div>
          <h1 className={styles.title}>ASK VOICERA</h1>
          <button
            className={styles.transcriptionButton}
            onClick={() => {
              setPosition(-100);
              setIsSecondScreenActive(true);
            }}
            onMouseEnter={() => speak("Start Chat")}
          >
            Start Chat
          </button>
          <p
            style={{ color: "#999", fontSize: "0.875rem", marginTop: "1rem" }}
            onMouseEnter={() => speak("Swipe up or tap button to open chat")}
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
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <button
              onClick={handleGoBack}
              style={{
                background: "none",
                border: "none",
                color: "white",
                fontSize: "1.5rem",
                cursor: "pointer",
                padding: "0.5rem",
              }}
              aria-label="Go back"
              onMouseEnter={() => speak("Go back")}
            >
              ←
            </button>
            <h1 className={styles.titleLarge}>Chat with Voicera</h1>
          </div>

          <div className={styles.chatArea}>
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`${styles.chatMessage} ${
                  msg.sender === "user" ? styles.user : styles.ai
                }`}
              >
                <span
                  className={styles.chatBubble}
                  tabIndex={0}
                  onMouseEnter={() =>
                    speak(
                      msg.sender === "user"
                        ? `You said: ${msg.text}`
                        : `AI says: ${msg.text}`
                    )
                  }
                  onFocus={() =>
                    speak(
                      msg.sender === "user"
                        ? `You said: ${msg.text}`
                        : `AI says: ${msg.text}`
                    )
                  }
                >
                  {msg.text}
                </span>
              </div>
            ))}
            {waiting && (
              <div className={`${styles.chatMessage} ${styles.ai}`}>
                <div
                  className={styles.typingIndicator}
                  tabIndex={0}
                  onMouseEnter={() => speak("AI is typing")}
                  onFocus={() => speak("AI is typing")}
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
              placeholder="Type your message..."
              className={styles.chatInput}
              disabled={waiting}
              onMouseEnter={() => speak("Type your message")}
              onFocus={() => speak("Type your message")}
            />
            <button
              type="submit"
              className={styles.transcriptionButton}
              disabled={waiting || !input.trim()}
              style={{ flexShrink: 0 }}
              onMouseEnter={() => speak("Send message")}
              onFocus={() => speak("Send message")}
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

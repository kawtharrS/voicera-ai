import styles from "./chat.module.css";
import { useSwipeScreen } from "../../hooks/useSwipeScreen";
import { useAudioTTS } from "../../hooks/useAudioTTS";
import { useChat } from "../../hooks/useChat";
import api from "../../api/axios";
import { useState, useRef, useEffect, useCallback } from "react";

const MicIcon = ({ className }: { className?: string }) => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" y1="19" x2="12" y2="23" />
    <line x1="8" y1="23" x2="16" y2="23" />
  </svg>
);

export default function VoiceraSwipeScreen() {
  const [roleId, setRoleId] = useState<number | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [finalTranscript, setInterimTranscriptFinal] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [aiIsSpeaking, setAiIsSpeaking] = useState(false);
  const recentlyDragged = useRef(false);
  const recognitionRef = useRef<any>(null);

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
    (text, category) => {
      setAiIsSpeaking(true);
      speak(text, category);
      setTimeout(() => setAiIsSpeaking(false), text.length * 100);
    }
  );

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition || recognitionRef.current) return;

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onstart = () => setIsRecording(true);
    rec.onresult = (e: any) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const transcript = e.results[i][0].transcript;
        if (e.results[i].isFinal) setInterimTranscriptFinal((prev) => prev + transcript + " ");
        else interim += transcript;
      }
      setInterimTranscript(interim);
    };
    rec.onerror = () => setIsRecording(false);
    rec.onend = () => setIsRecording(false);

    recognitionRef.current = rec;
  }, []);


  const startRecording = useCallback(() => {
    if (recognitionRef.current && !isRecording) {
      setInterimTranscriptFinal("");
      setInterimTranscript("");
      recognitionRef.current.start();
    }
  }, [isRecording]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
    }
  }, [isRecording]);

  const handleSendVoice = async () => {
    const fullText = (finalTranscript + interimTranscript).trim();
    if (fullText) {
      setIsSending(true);
      try {
        await sendMessage(fullText);
        setInterimTranscriptFinal("");
        setInterimTranscript("");
      } finally {
        setIsSending(false);
      }
    }
  };

  const handleToggleVoice = () => {
    if (recentlyDragged.current) return;
    if (isRecording) {
      stopRecording();
      setTimeout(handleSendVoice, 500);
    } else {
      startRecording();
    }
  };

  const getCategoryColor = (cat?: string) => {
    const colors: Record<string, string> = { study: "#4db6ac", work: "#FF9800", personal: "#8b7ab8" };
    return colors[cat || ""] || "#999";
  };


  useEffect(() => {
    api.get("/user").then(r => setRoleId(r.data.role_id || 1)).catch(() => setRoleId(1));
  }, []);

  if (roleId === null) return <div className={styles.loadingContainer}><div className={styles.loader}></div></div>;

  const isThinking = waiting || isSending;

  if (roleId === 2) {
    return (
      <div
        className={`${styles.voiceraContainer} ${isDragging ? styles.dragging : ''}`}
        onTouchStart={(e) => { recentlyDragged.current = false; handleTouchStart(e); }}
        onTouchMove={handleTouchMove}
        onTouchEnd={() => { handleTouchEnd(); setTimeout(() => { if (!isDragging) recentlyDragged.current = false; }, 100); }}
        onMouseDown={(e) => { recentlyDragged.current = false; handleMouseDown(e); }}
        onMouseMove={(e) => { if (isDragging) recentlyDragged.current = true; handleMouseMove(e); }}
        onMouseUp={() => { handleMouseUp(); setTimeout(() => { if (!isDragging) recentlyDragged.current = false; }, 100); }}
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
            <h1 className={styles.title} onClick={() => speak("Ask Voicera")}>ASK VOICERA</h1>
            <button
              className={styles.transcriptionButton}
              onClick={() => {
                openSecondScreen();
                speak("Start Chat");
              }}
              onMouseEnter={() => { }}
            >
              Start Chat
            </button>
            <p className={styles.swipeHintText} onClick={() => speak("Swipe up or tap button to open chat")}>
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
            <header className={styles.chatHeader}>
              <button
                onClick={closeSecondScreen}
                className={styles.backButton}
                onMouseEnter={() => { }}
              >←</button>
              <h1 className={styles.titleLarge} onClick={() => speak("Chat with Voicera")}>Chat with Voicera</h1>
              {currentCategory && (
                <div className={styles.categoryBadge} style={{ backgroundColor: getCategoryColor(currentCategory) }} onClick={() => speak(`Mode: ${currentCategory}`)}>
                  {currentCategory}
                </div>
              )}
            </header>

            <div className={styles.chatArea}>
              {messages.map((msg: any, i) => (
                <div key={i} className={`${styles.chatMessage} ${msg.sender === "user" ? styles.user : styles.ai}`}>
                  <div
                    className={styles.chatBubble}
                    onClick={() => speak(msg.sender === "user" ? `You said: ${msg.text}` : `Voicera said: ${msg.text}`)}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
              {waiting && (
                <div className={`${styles.chatMessage} ${styles.ai}`}>
                  <div className={styles.typingIndicator} onClick={() => speak("Voicera is typing")}>
                    <div className={styles.typingDot}></div>
                    <div className={styles.typingDot}></div>
                    <div className={styles.typingDot}></div>
                  </div>
                </div>
              )}
            </div>

            <form className={styles.chatForm} onSubmit={(e) => { e.preventDefault(); if (input.trim()) sendMessage(input); }}>
              <input
                className={styles.chatInput}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                disabled={waiting}
                onMouseEnter={() => { }}
                onFocus={() => { }}
              />
              <button
                type="button"
                className={`${styles.micButton} ${isRecording ? styles.recording : ""}`}
                onMouseDown={startRecording}
                onMouseUp={() => { stopRecording(); setTimeout(handleSendVoice, 500); }}
                onTouchStart={startRecording}
                onTouchEnd={() => { stopRecording(); setTimeout(handleSendVoice, 500); }}
                disabled={waiting || isSending}
                onMouseEnter={() => { }}
              >
                <MicIcon />
              </button>
              <button
                type="submit"
                className={styles.sendButton}
                disabled={!input.trim() || waiting}
                onMouseEnter={() => { }}
              >Send</button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`${styles.voiceraContainer} ${isDragging ? styles.dragging : ''}`}
      onTouchStart={(e) => { recentlyDragged.current = false; handleTouchStart(e); }}
      onTouchMove={handleTouchMove}
      onTouchEnd={() => { handleTouchEnd(); setTimeout(() => { if (!isDragging) recentlyDragged.current = false; }, 100); }}
      onMouseDown={(e) => { recentlyDragged.current = false; handleMouseDown(e); }}
      onMouseMove={(e) => { if (isDragging) recentlyDragged.current = true; handleMouseMove(e); }}
      onMouseUp={() => { handleMouseUp(); setTimeout(() => { if (!isDragging) recentlyDragged.current = false; }, 100); }}
      onMouseLeave={() => isDragging && handleMouseUp()}
    >
      <div
        className={styles.screenFirst}
        style={{ transform: `translateY(${position}%)`, opacity: position === -100 ? 0 : 1 }}
      >
        <div className={styles.voiceModeContent} onClick={handleToggleVoice}>
          {isThinking ? (
            <div className={styles.logoContainer}>
              <img src="/image.png" alt="Voicera logo" className={styles.logoIcon} />
            </div>
          ) : (
            <div
              className={`${styles.orbContainer} ${isRecording ? styles.recording : ""} ${aiIsSpeaking ? styles.speaking : ""} ${isSending ? styles.thinking : ""}`}
              style={{
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={() => { }}
            >
              <div
                className={styles.orbInner}
                style={{
                  backgroundColor: aiIsSpeaking
                    ? '#5eadad'
                    : isSending
                    ? '#FFB74D'
                    : isRecording
                    ? '#ff5e5e'
                    : '#8b7ab8',
                }}
              ></div>
              <div className={styles.orbGlow}></div>
            </div>
          )}

          {/* Middle: Voicera title and instruction */}
          {!isRecording && !aiIsSpeaking && (
            <div
              className={`${styles.transcriptionDisplay} ${
                isThinking ? styles.blurred : ""
              }`}
            >
              <div className={styles.introCenter}>
                <h1 className={styles.title} onClick={() => speak('Voicera')}>
                  VOICERA
                </h1>
                <p
                  className={styles.instructionText}
                  onClick={() => speak('Tap orb to speak')}
                >
                  Tap orb to speak
                </p>
              </div>
            </div>
          )}

          <div
            className={`${styles.swipeHint} ${isThinking ? styles.blurred : ""}`}
            onClick={(e) => {
              e.stopPropagation();
              openSecondScreen();
            }}
            onMouseEnter={() => { }}
          >
            <p>History</p>
            <span>↑</span>
          </div>
        </div>
      </div>

      <div
        className={styles.screenSecond}
        style={{ transform: `translateY(${100 + position}%)` }}
      >
        <div className={styles.screenSecondContent}>
          <header className={styles.chatHeader}>
            <button onClick={closeSecondScreen} className={styles.backButton} onMouseEnter={() => { }}>←</button>
            <h1 className={styles.titleLarge} onClick={() => speak("Interaction History")}>History</h1>
            {currentCategory && (
              <div
                className={styles.categoryBadge}
                style={{ backgroundColor: getCategoryColor(currentCategory) }}
                onMouseEnter={() => { }}
              >
                {currentCategory}
              </div>
            )}
          </header>

          <div className={styles.chatArea}>
            {messages.map((msg, i) => (
              <div key={i} className={`${styles.chatMessage} ${msg.sender === "user" ? styles.user : styles.ai}`}>
                <div
                  className={styles.chatBubble}
                  onClick={() => speak(msg.sender === "user" ? `You said: ${msg.text}` : `Voicera said: ${msg.text}`)}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {waiting && (
              <div className={`${styles.chatMessage} ${styles.ai}`}>
                <div
                  className={styles.typingIndicator}
                  onClick={() => speak("AI is thinking")}
                >
                  <div className={styles.typingDot}></div>
                  <div className={styles.typingDot}></div>
                  <div className={styles.typingDot}></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
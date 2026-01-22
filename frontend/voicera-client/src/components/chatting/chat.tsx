import styles from "./chat.module.css";
import { useSwipeScreen } from "../../hooks/useSwipeScreen";
import { useAudioTTS } from "../../hooks/useAudioTTS";
import { useChat } from "../../hooks/useChat";
import api from "../../api/axios";
import { useState, useRef, useEffect, useCallback } from "react";
import { MicIcon } from "./mic_icon";


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
            <h1
              className={styles.title}
              onClick={() => speak("Ask Voicera")}
              data-sr="true"
              data-sr-label="Ask Voicera. Tap Start Chat to begin a conversation."
            >
              ASK VOICERA
            </h1>
            <button
              className={styles.transcriptionButton}
              onClick={() => {
                openSecondScreen();
                speak("Start Chat");
              }}
              onMouseEnter={() => { }}
              data-sr="true"
              data-sr-label="Start Chat button. Opens the chat screen."
            >
              Start Chat
            </button>
            <p
              className={styles.swipeHintText}
              onClick={() => speak("Swipe up or tap button to open chat")}
              data-sr="true"
              data-sr-label="Swipe up or tap Start Chat to open the chat."
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
            <header className={styles.chatHeader}>
              <button
                onClick={closeSecondScreen}
                className={styles.backButton}
                onMouseEnter={() => { }}
                data-sr="true"
                data-sr-label="Back button. Returns to Ask Voicera screen."
              >
                ←
              </button>
              <h1
                className={styles.titleLarge}
                onClick={() => speak("Chat with Voicera")}
                data-sr="true"
                data-sr-label="Chat with Voicera. Conversation view."
              >
                Chat with Voicera
              </h1>
              {currentCategory && (
                <div
                  className={styles.categoryBadge}
                  style={{ backgroundColor: getCategoryColor(currentCategory) }}
                  onClick={() => speak(`Mode: ${currentCategory}`)}
                  data-sr="true"
                  data-sr-label={`Current mode: ${currentCategory}`}
                >
                  {currentCategory}
                </div>
              )}
            </header>

            <div className={styles.chatArea}>
              {messages.map((msg: any, i) => (
                <div
                  key={i}
                  className={`${styles.chatMessage} ${msg.sender === "user" ? styles.user : styles.ai}`}
                >
                  <div
                    className={styles.chatBubble}
                    onClick={() => speak(msg.sender === "user" ? `You said: ${msg.text}` : `Voicera said: ${msg.text}`)}
                    data-sr="true"
                    data-sr-label={msg.sender === "user" ? `You said: ${msg.text}` : `Voicera said: ${msg.text}`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
              {waiting && (
                <div className={`${styles.chatMessage} ${styles.ai}`}>
                  <div
                    className={styles.typingIndicator}
                    onClick={() => speak("Voicera is typing")}
                    data-sr="true"
                    data-sr-label="Voicera is typing."
                  >
                    <div className={styles.typingDot}></div>
                    <div className={styles.typingDot}></div>
                    <div className={styles.typingDot}></div>
                  </div>
                </div>
              )}
            </div>

            <form
              className={styles.chatForm}
              onSubmit={(e) => { e.preventDefault(); if (input.trim()) sendMessage(input); }}
            >
              <input
                className={styles.chatInput}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                disabled={waiting}
                onMouseEnter={() => { }}
                onFocus={() => { }}
                data-sr="true"
                data-sr-label="Message input. Type your message here."
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
                data-sr="true"
                data-sr-label={isRecording ? "Recording voice. Release to send." : "Hold to record voice message."}
              >
              <MicIcon />
              </button>
              <button
                type="submit"
                className={styles.sendButton}
                disabled={!input.trim() || waiting}
                onMouseEnter={() => { }}
                data-sr="true"
                data-sr-label="Send button. Sends the typed message."
              >
                Send
              </button>
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
              data-sr="true"
              data-sr-label={
                aiIsSpeaking
                  ? "Voicera is speaking."
                  : isSending
                  ? "Voicera is thinking."
                  : isRecording
                  ? "Recording. Tap again to stop and send your message."
                  : "Voicera orb. Tap to start speaking."
              }
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
                <h1
                  className={styles.title}
                  onClick={() => speak('Voicera')}
                  data-sr="true"
                  data-sr-label="Voicera. Tap orb to speak."
                >
                  VOICERA
                </h1>
                <p
                  className={styles.instructionText}
                  onClick={() => speak('Tap orb to speak')}
                  data-sr="true"
                  data-sr-label="Tap the orb to start speaking."
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
            data-sr="true"
            data-sr-label="History. Swipe up or tap to see previous interactions."
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
            <button
              onClick={closeSecondScreen}
              className={styles.backButton}
              onMouseEnter={() => { }}
              data-sr="true"
              data-sr-label="Back button. Returns to the main Voicera screen."
            >
              ←
            </button>
            <h1
              className={styles.titleLarge}
              onClick={() => speak("Interaction History")}
              data-sr="true"
              data-sr-label="Interaction history. List of previous conversations."
            >
              History
            </h1>
            {currentCategory && (
              <div
                className={styles.categoryBadge}
                style={{ backgroundColor: getCategoryColor(currentCategory) }}
                onMouseEnter={() => { }}
                data-sr="true"
                data-sr-label={`Current mode: ${currentCategory}`}
              >
                {currentCategory}
              </div>
            )}
          </header>

          <div className={styles.chatArea}>
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`${styles.chatMessage} ${msg.sender === "user" ? styles.user : styles.ai}`}
              >
                <div
                  className={styles.chatBubble}
                  onClick={() => speak(msg.sender === "user" ? `You said: ${msg.text}` : `Voicera said: ${msg.text}`)}
                  data-sr="true"
                  data-sr-label={msg.sender === "user" ? `You said: ${msg.text}` : `Voicera said: ${msg.text}`}
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
                  data-sr="true"
                  data-sr-label="AI is thinking."
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

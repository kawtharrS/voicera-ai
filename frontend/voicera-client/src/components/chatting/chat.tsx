import styles from "./chat.module.css";
import { useSwipeScreen } from "../../hooks/useSwipeScreen";
import { useAudioTTS } from "../../hooks/useAudioTTS";
import { useChat } from "../../hooks/useChat";
import { useSpeechRecognition } from "../../hooks/useSpeechRecognition";
import { useChatHandlers } from "../../hooks/useChatHandlers";
import api from "../../api/axios";
import { useState, useRef, useEffect } from "react";
import { MicIcon } from "./mic_icon";
import { ImageIcon } from "./image_icon";
import type { ChangeEvent } from "react";

export default function VoiceraSwipeScreen() {
  const [aiIsSpeaking, setAiIsSpeaking] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isDescribingImage, setIsDescribingImage] = useState(false);

  const { speak } = useAudioTTS(null);

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

  const {
    input,
    setInput,
    messages,
    waiting,
    currentCategory,
    sendMessage,
    addMessage,
  } = useChat((text, category) => {
    setAiIsSpeaking(true);
    speak(text, category);
    setTimeout(() => setAiIsSpeaking(false), text.length * 100);
  });

  const {
    isRecording,
    interimTranscript,
    finalTranscript,
    startRecording,
    stopRecording,
    resetTranscript,
  } = useSpeechRecognition();

  // Open the image picker/gallery only when the user presses the "f" key.
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() !== "f") return;

      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return;
      }

      if (!isDescribingImage && fileInputRef.current) {
        fileInputRef.current.click();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isDescribingImage]);

  const {
    roleId,
    isSending,
    handleSendVoice,
    handleToggleVoice,
    updateRecentlyDragged,
  } = useChatHandlers({
    sendMessage,
    startRecording,
    stopRecording,
    resetTranscript,
    finalTranscript,
    interimTranscript,
    isRecording,
  });

  const handleImageSelected = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsDescribingImage(true);
    try {
      const reader = new FileReader();
      const imageUrlPromise = new Promise<string>((resolve) => {
        reader.onloadend = () => resolve(reader.result as string);
      });
      reader.readAsDataURL(file);
      const dataUrl = await imageUrlPromise;

      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post<any>("/image/describe", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const responseData = response.data;
      const data = responseData.data || responseData;
      const description = data.description || "I couldn't describe the image.";
      addMessage("user", "What's in this image?", "image", dataUrl);
      addMessage("ai", description, "image");
      speak(description, "image");
    } catch (error) {
      console.error("Error describing image", error);
      addMessage("ai", "Sorry, I couldn't describe that image.", "error");
      speak("Sorry, I couldn't describe that image.", "error");
    } finally {
      setIsDescribingImage(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const getCategoryColor = (cat?: string) => {
    const colors: Record<string, string> = { study: "#4db6ac", work: "#FF9800", personal: "#8b7ab8" };
    return colors[cat || ""] || "#999";
  };

  if (roleId === null) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loader}></div>
      </div>
    );
  }

  const isThinking = waiting || isSending;

  if (roleId === 2) {
    return (
      <div
        className={`${styles.voiceraContainer} ${isDragging ? styles.dragging : ""}`}
        onTouchStart={(e) => {
          updateRecentlyDragged(false);
          handleTouchStart(e);
        }}
        onTouchMove={handleTouchMove}
        onTouchEnd={() => {
          handleTouchEnd();
          setTimeout(() => {
            if (!isDragging) updateRecentlyDragged(false);
          }, 100);
        }}
        onMouseDown={(e) => {
          updateRecentlyDragged(false);
          handleMouseDown(e);
        }}
        onMouseMove={(e) => {
          if (isDragging) updateRecentlyDragged(true);
          handleMouseMove(e);
        }}
        onMouseUp={() => {
          handleMouseUp();
          setTimeout(() => {
            if (!isDragging) updateRecentlyDragged(false);
          }, 100);
        }}
        onMouseLeave={() => isDragging && handleMouseUp()}
      >
        <input
          type="file"
          accept="image/*"
          capture="environment"
          ref={fileInputRef}
          onChange={handleImageSelected}
          style={{ display: "none" }}
        />
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
                  className={`${styles.chatMessage} ${msg.sender === "user" ? styles.user : styles.ai
                    }`}
                >
                  <div
                    className={styles.chatBubble}
                    onClick={() =>
                      speak(
                        msg.sender === "user"
                          ? `You said: ${msg.text}`
                          : `Voicera said: ${msg.text}`,
                      )
                    }
                    data-sr="true"
                    data-sr-label={
                      msg.sender === "user"
                        ? `You said: ${msg.text}`
                        : `Voicera said: ${msg.text}`
                    }
                  >
                    {msg.imageUrl && (
                      <img src={msg.imageUrl} alt="Uploaded" className={styles.chatImage} />
                    )}
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
                  </div>
                </div>
              )}
              {isDescribingImage && (
                <div className={`${styles.chatMessage} ${styles.ai}`}>
                  <div
                    className={styles.typingIndicator}
                    style={{ backgroundColor: "#FF9800" }}
                  >
                    <span>Describing image...</span>
                    <div className={styles.typingDot}></div>
                  </div>
                </div>
              )}
            </div>

            <form
              className={styles.chatForm}
              onSubmit={(e) => {
                e.preventDefault();
                if (input.trim()) sendMessage(input);
              }}
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
                onMouseUp={() => {
                  stopRecording();
                  setTimeout(handleSendVoice, 500);
                }}
                onTouchStart={startRecording}
                onTouchEnd={() => {
                  stopRecording();
                  setTimeout(handleSendVoice, 500);
                }}
                disabled={waiting || isSending}
                onMouseEnter={() => { }}
                data-sr="true"
                data-sr-label={
                  isRecording
                    ? "Recording voice. Release to send."
                    : "Hold to record voice message."
                }
              >
                <MicIcon />
              </button>
              <button
                type="button"
                className={styles.micButton}
                onClick={() => fileInputRef.current?.click()}
                disabled={waiting || isSending || isDescribingImage}
                title="Upload Image"
              >
                <ImageIcon />
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
      </div >
    );
  }

  return (
    <div
      className={`${styles.voiceraContainer} ${isDragging ? styles.dragging : ""}`}
      onTouchStart={(e) => {
        updateRecentlyDragged(false);
        handleTouchStart(e);
      }}
      onTouchMove={handleTouchMove}
      onTouchEnd={() => {
        handleTouchEnd();
        setTimeout(() => {
          if (!isDragging) updateRecentlyDragged(false);
        }, 100);
      }}
      onMouseDown={(e) => {
        updateRecentlyDragged(false);
        handleMouseDown(e);
      }}
      onMouseMove={(e) => {
        if (isDragging) updateRecentlyDragged(true);
        handleMouseMove(e);
      }}
      onMouseUp={() => {
        handleMouseUp();
        setTimeout(() => {
          if (!isDragging) updateRecentlyDragged(false);
        }, 100);
      }}
      onMouseLeave={() => isDragging && handleMouseUp()}
    >
      <input
        type="file"
        accept="image/*"
        capture="environment"
        ref={fileInputRef}
        onChange={handleImageSelected}
        style={{ display: "none" }}
      />
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
              className={`${styles.orbContainer} ${isRecording ? styles.recording : ""
                } ${aiIsSpeaking ? styles.speaking : ""} ${isSending ? styles.thinking : ""}`}
              style={{
                transition: "all 0.3s ease",
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
                    ? "#5eadad"
                    : isSending
                      ? "#FFB74D"
                      : isRecording
                        ? "#FFB74D"
                        : "#8b7ab8",
                }}
              ></div>
              <div className={styles.orbGlow}></div>
            </div>
          )}

          {!isRecording && !aiIsSpeaking && (
            <div
              className={`${styles.transcriptionDisplay} ${isThinking ? styles.blurred : ""
                }`}
            >
              <div className={styles.introCenter}>
                <h1
                  className={styles.title}
                  onClick={() => speak("Voicera")}
                  data-sr="true"
                  data-sr-label="Voicera. Tap orb to speak."
                >
                  VOICERA
                </h1>
                <p
                  className={styles.instructionText}
                  onClick={() => speak("Tap orb to speak")}
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
                className={`${styles.chatMessage} ${msg.sender === "user" ? styles.user : styles.ai
                  }`}
              >
                <div
                  className={styles.chatBubble}
                  onClick={() =>
                    speak(
                      msg.sender === "user"
                        ? `You said: ${msg.text}`
                        : `Voicera said: ${msg.text}`,
                    )
                  }
                  data-sr="true"
                  data-sr-label={
                    msg.sender === "user"
                      ? `You said: ${msg.text}`
                      : `Voicera said: ${msg.text}`
                  }
                >
                  {msg.imageUrl && (
                    <img src={msg.imageUrl} alt="Uploaded" className={styles.chatImage} />
                  )}
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

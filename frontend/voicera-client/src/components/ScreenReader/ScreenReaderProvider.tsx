import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { useAudioTTS } from "../../hooks/useAudioTTS";
import styles from "./ScreenReader.module.css";
import type {ScreenReaderContextValue} from "./type";

const ScreenReaderContext = createContext<ScreenReaderContextValue | undefined>(undefined);
const HIGHLIGHT_CLASS = styles.highlight;

export const useScreenReader = () => {
  const ctx = useContext(ScreenReaderContext);
  if (!ctx) {
    throw new Error("useScreenReader must be used within ScreenReaderProvider");
  }
  return ctx;
};

export const ScreenReaderProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const { speak } = useAudioTTS("screenreader");
  const [enabled, setEnabled] = useState(false);
  const currentElementRef = useRef<HTMLElement | null>(null);
  const currentIndexRef = useRef<number>(-1);
  const clearHighlight = () => {
    if (currentElementRef.current) {
      currentElementRef.current.classList.remove(HIGHLIGHT_CLASS);
      currentElementRef.current = null;
    }
    currentIndexRef.current = -1;
  };
  const toggle = () => {
    setEnabled((prev) => {
      const next = !prev;
      if (!next) {
        clearHighlight();
        speak("Screen reader off", "screenreader");
      } else {
        speak(
          "Screen reader on. Use up and down arrow keys to move between elements.",
          "screenreader"
        );
      }
      return next;
    });
  };
  const focusElement = (el: HTMLElement | null) => {
    if (currentElementRef.current) {
      currentElementRef.current.classList.remove(HIGHLIGHT_CLASS);
    }
    currentElementRef.current = el;

    if (el) {
      el.classList.add(HIGHLIGHT_CLASS);
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      const label =
        el.getAttribute("data-sr-label") ||
        el.getAttribute("aria-label") ||
        el.textContent ||
        "";
      const text = label.trim();
      if (text) {
        speak(text, "screenreader");
      }
    }
  };

  const moveFocus = (direction: 1 | -1) => {
    const selector = "[data-sr]";
    const elements = Array.from(
      document.querySelectorAll<HTMLElement>(selector)
    );
    if (!elements.length) return;

    let nextIndex = currentIndexRef.current + direction;
    if (nextIndex < 0) nextIndex = elements.length - 1;
    if (nextIndex >= elements.length) nextIndex = 0;

    currentIndexRef.current = nextIndex;
    focusElement(elements[nextIndex]);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && e.shiftKey && (e.key === "S" || e.key === "s")) {
        e.preventDefault();
        toggle();
        return;
      }
      if (!enabled) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        moveFocus(1);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        moveFocus(-1);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [enabled]);

  useEffect(() => {
    if (!enabled) {
      clearHighlight();
    } else {
      setTimeout(() => moveFocus(1), 0);
    }
  }, [enabled]);

  return (
    <ScreenReaderContext.Provider value={{ enabled, toggle }}>
      {children}
      <div className={styles.container} aria-live="polite" aria-label="Screen reader controls">
        <button
          type="button"
          onClick={toggle}
          className={styles.toggleButton}
        >
          {enabled ? "Screen Reader: On" : "Screen Reader: Off"}
        </button>
      </div>
    </ScreenReaderContext.Provider>
  );
};

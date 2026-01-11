import React from "react";
import styles from "./Showcase.module.css";

const Showcase: React.FC = () => {
  return (
    <section className={styles.showcase}>
      <div className={styles.imageSection}>
        <div className={styles.personImage}>
          <div className={styles.personPlaceholder}>
            <svg
              width="300"
              height="350"
              viewBox="0 0 300 350"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Person with headphones illustration */}
              <ellipse cx="150" cy="320" rx="100" ry="30" fill="#d4956a" />
              <rect
                x="100"
                y="180"
                width="100"
                height="140"
                rx="10"
                fill="#87CEEB"
              />
              <circle cx="150" cy="120" r="60" fill="#d4a574" />
              <circle cx="150" cy="110" r="50" fill="#e8c4a0" />
              {/* Hair */}
              <path
                d="M100 100 Q150 40 200 100"
                fill="#4a3728"
                stroke="#4a3728"
                strokeWidth="20"
              />
              {/* Face */}
              <circle cx="130" cy="105" r="5" fill="#333" />
              <circle cx="170" cy="105" r="5" fill="#333" />
              <path
                d="M135 130 Q150 145 165 130"
                stroke="#333"
                strokeWidth="3"
                fill="none"
              />
              {/* Headphones */}
              <path
                d="M85 110 Q85 50 150 50 Q215 50 215 110"
                stroke="#333"
                strokeWidth="12"
                fill="none"
                strokeLinecap="round"
              />
              <rect x="75" y="100" width="25" height="45" rx="8" fill="#333" />
              <rect x="200" y="100" width="25" height="45" rx="8" fill="#333" />
              <rect
                x="78"
                y="105"
                width="19"
                height="35"
                rx="6"
                fill="#ff9800"
              />
              <rect
                x="203"
                y="105"
                width="19"
                height="35"
                rx="6"
                fill="#ff9800"
              />
            </svg>
          </div>
        </div>
      </div>

      <div className={styles.appSection}>
        <div className={styles.phoneMockup}>
          <div className={styles.phoneNotch}></div>
          <div className={styles.phoneContent}>
            <div className={styles.appHeader}>
              <div className={styles.appLogo}></div>
              <span className={styles.appName}>Voice Assistant</span>
            </div>

            <div className={`${styles.chatBubble} ${styles.aiBubble}`}>
              Hello! How can I help you today?
            </div>

            <div className={`${styles.chatBubble} ${styles.userBubble}`}>
              What's the weather like?
            </div>

            <div className={`${styles.chatBubble} ${styles.aiBubble}`}>
              It's currently 72°F and sunny in your area.
            </div>

            <div className={styles.inputBar}>
              <span className={styles.inputPlaceholder}>Speak or type...</span>
              <div className={styles.micButton}>
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z"
                    fill="#ffffff"
                  />
                  <path
                    d="M19 10V12C19 15.87 15.87 19 12 19C8.13 19 5 15.87 5 12V10"
                    stroke="#ffffff"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Showcase;

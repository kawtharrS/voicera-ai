import React from "react";
import styles from "./Services.module.css";

const Services: React.FC = () => {
  const cards = [
    {
      title: "SERVICES",
      variantClass: styles.cardOrange,
      description:
        "Voicera is a voice-first AI assistant that helps you manage tasks and access information using only your voice. Built for accessibility, it delivers intelligent, hands-free assistance with clear spoken responses.",
      label: (
        <>
          Speak Your
          <br />
          Command
        </>
      ),
      icon: (
        <svg
          width="26"
          height="26"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M19 10V12C19 15.87 15.87 19 12 19C8.13 19 5 15.87 5 12V10"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M12 19V23"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M8 23H16"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      ),
    },
    {
      title: "ABOUT",
      variantClass: styles.cardPurple,
      description:
        "Voicera is a voice-first AI assistant that helps you manage tasks and access information using only your voice. Built for accessibility, it delivers intelligent, hands-free assistance with clear spoken responses.",
      label: (
        <>
          AI Understand
          <br />
          Intent
        </>
      ),
      icon: (
        <svg
          width="26"
          height="26"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="2"
          />
          <path
            d="M12 6V12L16 14"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle cx="12" cy="12" r="3" fill="currentColor" />
        </svg>
      ),
    },
    {
      title: "HOW TO USE",
      variantClass: styles.cardGreen,
      description:
        "Voicera is a voice-first AI assistant that helps you manage tasks and access information using only your voice. Built for accessibility, it delivers intelligent, hands-free assistance with clear spoken responses.",
      label: (
        <>
          Tasks
          <br />
          Automated
        </>
      ),
      icon: (
        <svg
          width="26"
          height="26"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M9 11L12 14L22 4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M21 12V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      ),
    },
  ];

  return (
    <section className={styles.services}>
      <div className={styles.cards}>
        {cards.map((card) => (
          <div key={card.title} className={styles.card}>
            <div className={`${styles.cardTop} ${card.variantClass}`}>
              <div className={styles.cardTitle}>{card.title}</div>
              <div className={styles.cardText}>{card.description}</div>
            </div>

            <div className={styles.cardBottom}>
              <div className={styles.bottomIcon}>{card.icon}</div>
              <div className={styles.bottomLabel}>{card.label}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Services;

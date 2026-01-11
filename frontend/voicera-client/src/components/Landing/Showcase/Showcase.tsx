import React from "react";
import styles from "./Showcase.module.css";

const Showcase: React.FC = () => {
  return (
    <section className={styles.wrapper}>
      <div className={styles.container}>
        <div className={styles.accessibilityBanner}>
          <h2 className={styles.bannerTitle}>
            Designed for Accessibility Perfect
            <br />
            for Students &amp; Workers
          </h2>
          <p className={styles.bannerSubtitle}>
            AI that understands everyone, built with WCAG standards
          </p>
          <div className={styles.bannerIcons} aria-hidden="true">
            <span className={styles.icon}>
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="currentColor"
              >
                <path d="M16 11c1.66 0 3-1.34 3-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3Zm-8 0c1.66 0 3-1.34 3-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3Zm8 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5Zm-8 0c-.29 0-.62.02-.97.06C5.13 13.24 2 14.34 2 16.5V19h5v-2.5c0-1.23.58-2.2 1.55-2.95-.21-.03-.4-.05-.55-.05Z" />
              </svg>
            </span>
            <span className={styles.icon}>
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="currentColor"
              >
                <path d="M4 5h16v10H4V5Zm0 12h6v2H4v-2Zm10 0h6v2h-6v-2Z" />
              </svg>
            </span>
            <span className={styles.icon}>
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="currentColor"
              >
                <path d="M18 2H8C6.9 2 6 2.9 6 4v16c0 1.1.9 2 2 2h10v-2H8V4h10V2Zm2 4H10c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2Zm0 16H10V8h10v14Z" />
              </svg>
            </span>
            <span className={styles.icon}>
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="currentColor"
              >
                <path d="M12 2a10 10 0 1 0 10 10A10.01 10.01 0 0 0 12 2Zm1 17.93c-2.83.48-5.5-.76-7.03-3.01H8v-2H4.69a7.96 7.96 0 0 1 0-2H8v-2H5.97c1.53-2.25 4.2-3.49 7.03-3.01V9h-2v2h2v2h-2v2h2v2h-2v2h2Z" />
              </svg>
            </span>
            <span className={styles.icon}>
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="currentColor"
              >
                <path d="M10 2h4v2h-4V2Zm-3 4h10v7c0 2.76-2.24 5-5 5s-5-2.24-5-5V6Zm5 14c3.87 0 7-3.13 7-7h2c0 4.97-4.03 9-9 9s-9-4.03-9-9h2c0 3.87 3.13 7 7 7Z" />
              </svg>
            </span>
          </div>
        </div>

        <div className={styles.main}>
          <div className={styles.pitch}>
            <h3 className={styles.heading}>Turn speech into action</h3>
            <p className={styles.lead}>
              Voicera helps you manage tasks, access information, and stay
              productive — using your voice.
            </p>
            <button type="button" className={styles.primaryBtn}>
              Get Started
            </button>
          </div>

          <div className={styles.featureCards}>
            <div className={styles.featureCard}>
              <div className={`${styles.featureTop} ${styles.topOrange}`}>
                Voice Commands
              </div>
              <div className={styles.featureBody}>
                Speak naturally to set reminders, open pages, and trigger
                actions.
              </div>
            </div>

            <div className={styles.featureCard}>
              <div className={`${styles.featureTop} ${styles.topPurple}`}>
                Smart Understanding
              </div>
              <div className={styles.featureBody}>
                Understands intent and responds with clear, simple guidance.
              </div>
            </div>

            <div className={styles.featureCard}>
              <div className={`${styles.featureTop} ${styles.topTeal}`}>
                Accessibility First
              </div>
              <div className={styles.featureBody}>
                Designed with contrast, spacing, and voice feedback for
                everyone.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Showcase;

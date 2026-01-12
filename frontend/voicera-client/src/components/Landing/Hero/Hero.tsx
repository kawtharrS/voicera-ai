import React from "react";
import styles from "./Hero.module.css";

interface HeroProps {
  onLoginClick?: () => void;
}

const Hero: React.FC<HeroProps> = ({onLoginClick}) => {
  return (
    <section className={styles.hero}>
      <div className={styles.content}>
        <h1 className={styles.title}>
          Voicera: Your AI
          <br />
          Voice Assistant
        </h1>
        <p className={styles.subtitle}>Speech into Action Effortlessly</p>
        <button className={styles.getStartedBtn} onClick={onLoginClick} >Get Started</button>
        <p className={styles.tagline}>Experience hands-free Productivity</p>
      </div>

      <div className={styles.imageContainer}>
        <div className={styles.heroImage}>
          <img
            src="/generated3.png"
            alt="Voicera AI Voice Assistant"
            className={styles.heroImg}
          />
        </div>
      </div>
    </section>
  );
};

export default Hero;

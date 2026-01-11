import React from "react";
import styles from "./Navbar.module.css";

interface NavbarProps {
  onSignUpClick?: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onSignUpClick }) => {
  return (
    <nav className={styles.navbar}>
      <a href="/" className={styles.logo}>
        <img
          className={styles.logoIcon}
            src="/image.png"
            alt="Voicera logo"
        />
        Voicera
      </a>

      <div className={styles.navLinks}>
        <a href="#features" className={styles.navLink}>
          Features
        </a>
        <a href="#accessibility" className={styles.navLink}>
          Accessibility
        </a>
        <a href="#contact" className={styles.navLink}>
          Contact
        </a>
      </div>

      <button className={styles.signUpBtn} onClick={onSignUpClick}>
        Sign Up
      </button>
    </nav>
  );
};

export default Navbar;

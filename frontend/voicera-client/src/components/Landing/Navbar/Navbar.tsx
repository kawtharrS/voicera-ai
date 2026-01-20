import React, { useState, useEffect } from "react";
import styles from "./Navbar.module.css";
import { Link, useNavigate } from "react-router-dom";

interface NavbarProps {
  onSignUpClick?: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onSignUpClick }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const loggedIn = window.localStorage.getItem("voicera_logged_in") === "true";
    setIsLoggedIn(loggedIn);
  }, []);

  const handleLogout = () => {
    window.localStorage.removeItem("voicera_logged_in");
    setIsLoggedIn(false);
    navigate("/");
  };

  return (
    <nav className={styles.navbar}>
      <Link to="/" className={styles.logo}>
        <img className={styles.logoIcon} src="/image.png" alt="Voicera logo" />
        Voicera
      </Link>

      <div className={styles.navLinks}>
        <a href="#features" className={styles.navLink}>
          Features
        </a>
        <a href="#accessibility" className={styles.navLink}>
          Accessibility
        </a>
        {isLoggedIn ? (
          <Link to="/chat" className={styles.navLink}>
            Chat Hub
          </Link>
        ) : (
          <a href="#contact" className={styles.navLink}>
            Contact
          </a>
        )}
      </div>

      <div className={styles.authActions}>
        {isLoggedIn ? (
          <button className={styles.logoutBtn} onClick={handleLogout}>
            Logout
          </button>
        ) : onSignUpClick ? (
          <button className={styles.signUpBtn} onClick={onSignUpClick}>
            Sign Up
          </button>
        ) : (
          <Link to="/signup" className={styles.signUpBtn}>
            Sign Up
          </Link>
        )}
      </div>
    </nav>
  );
};

export default Navbar;

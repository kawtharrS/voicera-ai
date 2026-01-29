import React, { useState } from "react";
import styles from "./Landing.module.css";
import Navbar from "./Navbar";
import Hero from "./Hero";
import Services from "./Services";
import Footer from "./Footer";
import Login from "../login";
import SignUp from "../signUp";

const Landing: React.FC = () => {
  const [showLogin, setLogin] = useState(false);
  const [showSignup, setSignup] = useState(false);

  if (showLogin) {
    return <Login onBack={() => setLogin(false)} />;
  }
  if (showSignup) {
    return <SignUp onBack={() => setSignup(false)} />;
  }

  return (
    <div className={styles.landing}>
      <Navbar onSignUpClick={() => setSignup(true)} />
      <Hero onLoginClick={() => setLogin(true)} />
      <Services />

      <Footer />
    </div>
  );
};

export default Landing;

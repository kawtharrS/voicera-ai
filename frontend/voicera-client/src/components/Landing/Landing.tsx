import React, { useState } from "react";
import styles from "./Landing.module.css";
import Navbar from "./Navbar";
import Hero from "./Hero";
import Services from "./Services";
import Footer from "./Footer";
import SignUp from "../SignUp";
import Login from "../Login";

const Landing: React.FC = () => {
  const [showSignUp, setShowSignUp] = useState(false);
  const [showLogin, setLogin] = useState(false);


  if (showSignUp) {
    return <SignUp onBack={() => setShowSignUp(false)} />;
  }
  if (showLogin) {
    return <Login onBack={() => setLogin(false)} />;
  }

  return (
    <div className={styles.landing}>
      <Navbar onSignUpClick={() => setShowSignUp(true)} />
      <Hero onLoginClick={() => setLogin(true)} />
      <Services />
      <Footer />
    </div>
  );
};

export default Landing;

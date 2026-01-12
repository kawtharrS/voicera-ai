export function speak(text: string) {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel(); 
    const utter = new window.SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utter);
  }
}
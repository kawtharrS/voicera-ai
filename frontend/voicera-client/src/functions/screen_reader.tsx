export async function speak(text: string) {
  if (!text) return;

  try {
    // Fetch audio from your FastAPI backend
    const res = await fetch(`/tts?text=${encodeURIComponent(text)}`);
    if (!res.ok) {
      console.error("TTS request failed");
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);

    // Create audio element and play
    const audio = new Audio(url);
    audio.play();

    // Optional: clean up after playback
    audio.onended = () => URL.revokeObjectURL(url);

  } catch (err) {
    console.error("Error playing TTS:", err);
  }
}

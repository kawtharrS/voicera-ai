from typing import Optional
import os 
from dotenv import load_dotenv
import requests

load_dotenv()

class MoodTool:
    def __init__(self):
        self._ngrok_url = os.getenv("NGROK_URL")

        if not self._ngrok_url:
            raise ValueError("NGROK_URL must be provided in environment variables")
        
        self._ngrok_url = self._ngrok_url.rstrip("/")
        self._endpoint = f"{self._ngrok_url}/predict"

    def detect_emotion(self, text: str) -> str:
        """
        Detect emotion from text and return only the emotion label
        """
        try:
            if not text or not isinstance(text, str):
                return "unknown"
            response = requests.post(
                self._endpoint,
                json={"text": text},
                timeout=10  
            )            
            response.raise_for_status()
            result = response.json()
            
            return result.get("emotion", "unknown")
            
        except Exception as e:
            print(f"[MoodTool Error] {str(e)}")
            return "unknown"


if __name__ == "__main__":
    tool = MoodTool()

    emotion = tool.detect_emotion("I'm so happy today!")
    print(f"Detected emotion: {emotion}")
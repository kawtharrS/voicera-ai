"""
File: langgraph/src/agents/emotion/nodes.py
FIXED VERSION - ensures emotion is passed through the entire state
"""

import os
from typing import Optional
from datetime import datetime

from colorama import Fore, Style

from ..agents.agent import EmotionAgent
from ..structure_outputs.structure_output import Emotion
from ..states.state import EmotionDetectionState


class EmotionDetectionNodes:
    """Nodes for detecting user emotion using LLM agent"""
    
    def __init__(self):
        self.emotion_agent = EmotionAgent()

    def receive_text(self, state: EmotionDetectionState) -> EmotionDetectionState:
        """Receive and prepare text for emotion detection."""
        print(Fore.CYAN + "Receiving text for emotion analysis..." + Style.RESET_ALL)

        text = state.get("text") or ""

        if not text:
            text = state.get("query") or ""

        if not text:
            current = state.get("current_interaction") or {}
            if isinstance(current, dict):
                text = (
                    current.get("student_question")
                    or current.get("user_request")
                    or ""
                )
            else:
                text = (
                    getattr(current, "student_question", "")
                    or getattr(current, "user_request", "")
                )

        if not text:
            print(Fore.YELLOW + "No text found in state for emotion analysis" + Style.RESET_ALL)

        timestamp = datetime.now().isoformat()

        return {
            "text": text,
            "timestamp": timestamp
        }

    def detect_emotion(self, state: EmotionDetectionState) -> EmotionDetectionState:
        """
        Detect emotion from text using EmotionAgent (LLM-based)
        IMPORTANT: Return detected_emotion so it persists through the workflow
        """
        print(Fore.CYAN + "Running EmotionAgent..." + Style.RESET_ALL)

        text = state.get("text") or ""
        
        if not text:
            print(Fore.YELLOW + "No text provided, defaulting to unknown emotion" + Style.RESET_ALL)
            return {
                "detected_emotion": Emotion.unknown,
                "emotion_output": {"emotion": "unknown"},
                "error": "No text provided"
            }

        try:
            result = self.emotion_agent.detect(text, None)
            
            print(Fore.GREEN + f"Detected emotion: {result.emotion.value}" + Style.RESET_ALL)
            
            return {
                "detected_emotion": result.emotion,
                "emotion_output": {
                    "emotion": result.emotion.value
                },
                "error": None
            }
            
        except Exception as e:
            print(Fore.RED + f"Emotion detection error: {e}" + Style.RESET_ALL)
            return {
                "detected_emotion": Emotion.unknown,
                "emotion_output": {"emotion": "unknown"},
                "error": str(e)
            }

    def track_emotion_history(self, state: EmotionDetectionState) -> EmotionDetectionState:
        """
        Track emotion changes over conversation history
        IMPORTANT: Preserve detected_emotion through the state
        """
        print(Fore.MAGENTA + "Tracking emotion history..." + Style.RESET_ALL)
        
        current_emotion = state.get("detected_emotion", Emotion.unknown)
        emotion_history = state.get("emotion_history", [])
        timestamp = state.get("timestamp")
        
        emotion_entry = {
            "emotion": current_emotion.value if hasattr(current_emotion, 'value') else str(current_emotion),
            "timestamp": timestamp
        }
        emotion_history.append(emotion_entry)
        
        if len(emotion_history) > 10:
            emotion_history = emotion_history[-10:]
        
        print(Fore.BLUE + f"Emotion history length: {len(emotion_history)}" + Style.RESET_ALL)
        
        return {
            "emotion_history": emotion_history,
            "detected_emotion": current_emotion 
        }

    def continue_chat(self, state: EmotionDetectionState) -> EmotionDetectionState:
        """
        Continue with normal chat processing
        CRITICAL: Return detected_emotion but don't include it in the response text
        """
        print(Fore.YELLOW + "Processing chat with emotion context..." + Style.RESET_ALL)
        
        emotion = state.get("detected_emotion", Emotion.unknown)
        text = state.get("text", "")
        emotion_history = state.get("emotion_history", [])
        
        emotion_value = emotion.value if hasattr(emotion, 'value') else str(emotion)
        
        print(Fore.BLUE + f"Current emotion: {emotion_value}" + Style.RESET_ALL)
        print(Fore.BLUE + f"Total emotions tracked: {len(emotion_history)}" + Style.RESET_ALL)

        ai_response = "How can I help you today?"
        
        return {
            "chat_processed": True,
            "ai_response": ai_response,
            "detected_emotion": emotion,
            "emotion_output": {"emotion": emotion_value}
        }
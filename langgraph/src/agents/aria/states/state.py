from typing import Optional, TypedDict, List
from enum import Enum


class Emotion(str, Enum):
    """Supported emotion categories"""
    joy = "joy"
    sadness = "sadness"
    anger = "anger"
    fear = "fear"
    surprise = "surprise"
    disgust = "disgust"
    neutral = "neutral"
    unknown = "unknown"


class EmotionEntry(TypedDict, total=False):
    """Single emotion history entry"""
    emotion: str
    timestamp: Optional[str]


class EmotionDetectionState(TypedDict, total=False):
    """State for emotion detection while maintaining normal chat flow"""
    
    text: Optional[str]
    current_interaction: Optional[str]
    
    detected_emotion: Optional[Emotion]
    emotion_output: Optional[dict]
    
    chat_processed: Optional[bool]
    ai_response: Optional[str]
    
    emotion_history: Optional[List[EmotionEntry]]
    timestamp: Optional[str]
    
    error: Optional[str]
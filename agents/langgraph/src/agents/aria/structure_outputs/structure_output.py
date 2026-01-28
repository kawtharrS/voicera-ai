from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class Emotion(str, Enum):
    joy = "joy"
    sadness = "sadness"
    anger = "anger"
    fear = "fear"
    surprise = "surprise"
    disgust = "disgust"
    neutral = "neutral"
    unknown = "unknown"


class EmotionDetectionOutput(BaseModel):
    emotion: Emotion = Field(
        ...,
        description="Detected emotion from the text"
    )


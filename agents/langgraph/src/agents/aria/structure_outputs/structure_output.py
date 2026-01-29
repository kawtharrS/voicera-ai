from pydantic import BaseModel, Field
from states.state import Emotion

class EmotionDetectionOutput(BaseModel):
    emotion: Emotion = Field(
        ...,
        description="Detected emotion from the text"
    )


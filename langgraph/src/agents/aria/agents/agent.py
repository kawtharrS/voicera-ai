import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from ..structure_outputs.structure_output import Emotion, EmotionDetectionOutput
from prompts.emotion import EMOTION_PROMPT

load_dotenv()

class EmotionAgent:
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.emotion_prompt = PromptTemplate(
            template=EMOTION_PROMPT,
            input_variables=["text", "preferences"]
        )
        
        self.emotion_runnable = (
            self.emotion_prompt
            | self.model.with_structured_output(EmotionDetectionOutput)
        )
    
    def detect(self, text: str, preferences: dict | None = None) -> EmotionDetectionOutput:
        """Detect emotion from text.

        Preferences are optional and used only to give the model extra
        context (e.g., language or tone), they do not change the schema.
        """
        pref_text = ""
        if preferences:
            lang = preferences.get("language") or preferences.get("lang") or "unspecified"
            tone = preferences.get("tone") or "unspecified"
            name = preferences.get("name") or preferences.get("agent_name") or "the assistant"
            extra = preferences.get("preference") or preferences.get("memory_notes") or ""
            pref_text = (
                f"Preferred language: {lang}\n"
                f"Preferred tone: {tone}\n"
                f"Agent name: {name}\n"
                f"Additional notes: {extra}"
            )

        result: EmotionDetectionOutput = self.emotion_runnable.invoke({
            "text": text,
            "preferences": pref_text,
        })
        return result

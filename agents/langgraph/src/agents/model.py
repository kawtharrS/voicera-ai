import os
from langchain_openai import ChatOpenAI

class Model:
    def __init__(self):
        self.openai_model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from .router_structure_output import ContinuationOutput
from prompts.router import CONTINUATION_PROMPT

load_dotenv()

class ContinuationAgent:
    def __init__(self):
        self.model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL"),
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.prompt = PromptTemplate(
            template=CONTINUATION_PROMPT,
            input_variables=["query", "has_study_plan", "has_calendar_result", "has_email_draft"]
        )
        
        self.runnable = (
            self.prompt
            | self.model.with_structured_output(ContinuationOutput)
        )

    def decide(self, query: str, has_study_plan: bool, has_calendar_result: bool, has_email_draft: bool) -> ContinuationOutput:
        """Decides whether to continue the workflow based on context"""
        return self.runnable.invoke({
            "query": query,
            "has_study_plan": "Yes, a study plan exists" if has_study_plan else "No study plan",
            "has_calendar_result": "Yes, calendar events were created" if has_calendar_result else "No calendar result yet",
            "has_email_draft": "Yes, an email draft exists" if has_email_draft else "No email draft"
        })

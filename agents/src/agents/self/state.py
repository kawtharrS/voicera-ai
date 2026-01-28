from typing import Optional, TypedDict, List

class PreferenceState(TypedDict, total=False):
    language: Optional[str]
    tone: Optional[str]
    name: Optional[str]
    preference: Optional[str]

class SelfAgentGraphState(TypedDict, total=False):
    user_id: Optional[int]
    preferences: Optional[PreferenceState]

    current_interaction: Optional[str]
    query: Optional[str]

    ai_response: Optional[str]
    observation: Optional[str]
    recommendations: Optional[List[str]]

    student_id: Optional[str]
    user_preferences: Optional[PreferenceState]
    query_category: Optional[str]
    route: Optional[str]
    
    router_output: Optional[dict]

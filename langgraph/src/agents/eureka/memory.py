import logging
from typing import Dict, Any
from .state import GraphState
from .agent import Agent
from .nodes import ClassroomNodes

logger = logging.getLogger(__name__)

class MemoryHandlers:    
    def __init__(self, agent: Agent):
        """Initialize with agent instance for memory access."""
        self.agent = agent
        self.nodes = ClassroomNodes()

    def receive_query_with_memory(self, state: GraphState) -> GraphState:
        """Receive query and add to conversation history.
        Extracts and saves any facts/information to langmem store.
        """
        query = None
        if "current_interaction" in state and isinstance(state["current_interaction"], dict):
            query = state["current_interaction"].get("student_question")
        
        if not query:
            logger.warning("No query found in state")
            return state
                
        self.agent.add_to_history("user", query)
        
        student_id = state.get("student_id")
        if student_id:
            self.agent.extract_and_save_to_langmem(query, student_id)
            
            student_context = self.agent.retrieve_from_langmem(student_id)
            state["student_context"] = student_context
    
        state["conversation_history"] = self.agent.get_history(k=1000)
        return state
    
    def categorize_with_memory(self, state: GraphState) -> GraphState:
        """Categorize query with conversation context.
        """
        query = None
        if "current_interaction" in state and isinstance(state["current_interaction"], dict):
            query = state["current_interaction"].get("student_question")
        
        if not query:
            state["query_category"] = "general"
            state["query_reasoning"] = ""
            return state
        
        try:
            result = self.agent.categorize_query.invoke({"query": query})
            state["query_category"] = result.category
            state["query_reasoning"] = getattr(result, "reasoning", "")
        except Exception as e:
            logger.error(f"Error categorizing query: {e}")
            state["query_category"] = "general"
            state["query_reasoning"] = ""
        
        return state
    
    def generate_with_memory(self, state: GraphState) -> GraphState:
        """Generate response using memory context.
        """
        try:
            result = self.nodes.generate_ai_response(state)
            
            interaction = result.get("current_interaction", {})
            ai_response = interaction.get("ai_response") if isinstance(interaction, dict) else getattr(interaction, "ai_response", "")
            
            if ai_response:
                self.agent.add_to_history("assistant", ai_response)
                logger.info(f"Response generated and added to memory: {len(ai_response)} chars")
            
            return result
            
        except Exception as e:
            return state

    
    def finalize_with_memory(self, state: GraphState) -> GraphState:
        """Finalize response and save to memory.
        """        
        final_response = state.get("final_response", state.get("ai_response", ""))
        
        if final_response:
            self.agent.add_to_history("assistant", final_response)

        query = None
        if "student_query" in state:
            query = state["student_query"]
        elif "current_interaction" in state and isinstance(state["current_interaction"], dict):
            query = state["current_interaction"].get("student_question")
        
        student_id = state.get("student_id")
        if student_id and state.get("query_category"):
            insight = (
                f"Student {student_id} asked about {state['query_category']}: "
                f"{query or 'unknown'}"
            )
            self.agent.save_student_insight(student_id, insight)        
        state["memory_updated"] = True
        
        return state
    
    def should_finalize(self, state: GraphState) -> str:
        """Decide whether to finalize or rewrite response
        """
        if state.get("sendable", False):
            logger.info("Response quality check PASSED - finalizing")
            return "end"
        
        trials = int(state.get("trials", 0))
        max_trials = int(state.get("max_trials", 3))
        
        if trials >= max_trials:
            return "end"
        
        logger.warning("Response quality check FAILED - rewriting...")
        return "rewrite"
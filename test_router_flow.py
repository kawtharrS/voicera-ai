import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "langgraph", "src"))

load_dotenv()

from agents.router.router_graph import graph

def test_router():
    print("Testing Router Integration...")
    
    # query = "what is mysql?" 
    # This should be categorized as 'study' and routed to Eureka
    
    initial_state = {
        "query": "what is mysql?",
        "question": "what is mysql?", # Eureka expects this sometimes as 'student_question' in interaction but checks 'question' too? 
        # Actually Eureka memory handler maps things. 
        # Let's check api/main.py initial state again to be consistent
        
        # Mimic API initial state
        "courses": [],
        "courseworks": [],
        "student_id": "test_student",
        "conversation_history": [],
        "current_interaction": {
             "student_question": "what is mysql?",
             "ai_response": "",
             "recommendations": []
        },
        "agent_messages": [],
        "sendable": False,
        "trials": 0,
        "max_trials": 3,
        "rewrite_feedback": "",
        "category": None
    }
    
    try:
        result = graph.invoke(initial_state, {"configurable": {"thread_id": "test_thread"}})
        
        print("\n--- Result ---")
        category = result.get("category")
        print(f"Category: {category}")
        
        interaction = result.get("current_interaction", {})
        if isinstance(interaction, dict):
             ai_response = interaction.get("ai_response")
        else:
             ai_response = getattr(interaction, "ai_response", "N/A")
             
        print(f"AI Response: {ai_response[:100]}...")
        
        if category == "study" and ai_response:
            print("\nSUCCESS: Routed to study and got response.")
        else:
            print("\nFAILURE: Did not route correctly or no response.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_router()

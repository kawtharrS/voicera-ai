import os
from colorama import Fore, Style
from typing import Optional
from langchain_openai import ChatOpenAI

from .agent import Agent
from .state import GraphState, Course, Coursework, CourseWorkMaterial, StudentInteraction
from tools.classroomTools import ClassroomTool
from tools.pdf_processor import PDFProcessor
from prompts.classroom import RELEVANT_COURSEWORK_PROMPT, AI_RESPONSE_PROMPT

openai_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)
class ClassroomNodes:
    def __init__(self):
        self.agents = Agent()
        self.classroom_tools = ClassroomTool()
        self.pdf_processor = PDFProcessor(self.classroom_tools)

    def _select_relevant_coursework(self, question: str, courseworks: list, llm) -> Optional[Coursework]:
        if not courseworks:
            return None
            
        items = [f"{i}. Title: {cw.title if isinstance(cw, Coursework) else cw.get('title', '')}\n   Description: {cw.description if isinstance(cw, Coursework) else cw.get('description', '')}" 
                 for i, cw in enumerate(courseworks)]

        response = llm.invoke(RELEVANT_COURSEWORK_PROMPT.format(
            question=question, coursework_list="\n".join(items)
        )).content.strip()

        if response.upper() == "NONE" or not response.isdigit():
            return None
            
        index = int(response)
        if 0 <= index < len(courseworks):
            cw = courseworks[index]
            return cw if isinstance(cw, Coursework) else Coursework(**cw)
        return None

    def load_courses(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Loading courses..." + Style.RESET_ALL)
        courses_list = self.classroom_tools.list_courses()
        
        requested_course_id = state["requested_course_id"]
        if requested_course_id:
            courses_list = [c for c in courses_list if str(c.get("id")) == str(requested_course_id)]
        
        return {"courses": [Course(**course) for course in courses_list]}

    def load_coursework(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Loading coursework..." + Style.RESET_ALL)
        courses = state.get("courses", [])
        all_coursework = []
        
        for course in courses:
            try:
                coursework_list = self.classroom_tools.list_coursework(course.id)
                all_coursework.extend(coursework_list)
            except Exception as e:
                print(Fore.RED + f"Could not load coursework for {course.name}: {str(e)}" + Style.RESET_ALL)
        
        return {"courseworks": [Coursework(**cw) for cw in all_coursework] if all_coursework else []}
    
    def load_and_index_materials(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Loading and indexing PDF materials..." + Style.RESET_ALL)
        courses = state.get("courses", [])
        all_materials = []
        total_stats = {"materials_processed": 0, "pdfs_found": 0, "chunks_indexed": 0}
        
        for course in courses:
            try:
                print(Fore.CYAN + f"Processing materials for {course.name}..." + Style.RESET_ALL)
                materials_list = self.classroom_tools.list_coursework_materials(course.id)
                all_materials.extend([CourseWorkMaterial(**m) for m in materials_list])
                
                stats = self.pdf_processor.process_course_materials(course.id)
                for key in total_stats:
                    total_stats[key] += stats[key]
                
                if stats["chunks_indexed"] > 0:
                    print(Fore.GREEN + f"{course.name}: {stats['pdfs_found']} PDFs, {stats['chunks_indexed']} new chunks indexed" + Style.RESET_ALL)
                else:
                    print(Fore.GREEN + f"{course.name}: {stats['pdfs_found']} PDFs already indexed" + Style.RESET_ALL)
                
            except Exception as e:
                print(Fore.RED + f"Could not process materials for {course.name}: {str(e)}" + Style.RESET_ALL)
        
        summary = "All materials already indexed (using cache)" if total_stats["chunks_indexed"] == 0 else f"Total: {total_stats['pdfs_found']} PDFs, {total_stats['chunks_indexed']} new chunks indexed"
        print(Fore.GREEN + f"\n{summary}" + Style.RESET_ALL)
        return {"materials": all_materials}

    def receive_student_query(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Receiving student query..." + Style.RESET_ALL)

        incoming = state["current_interaction"]
        question = incoming.get("student_question", "") if isinstance(incoming, dict) else incoming.student_question

        courses = state.get("courses", [])
        current_course = courses[0] if courses else None
        selected_coursework = self._select_relevant_coursework(question, state.get("courseworks", []), openai_model)
            
        return {"current_interaction": StudentInteraction(
            current_course=current_course,
            current_coursework=selected_coursework,
            student_question=question,
            ai_response="",
            recommendations=[]
        )}

    def categorize_student_query(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Categorizing student query..." + Style.RESET_ALL)

        query = state["current_interaction"].student_question


        result = self.agents.categorize_query.invoke({"query": query})
        category = result.category.value

        observation = f"Query classified as: {category}"
        print(Fore.GREEN + f"OBSERVATION: {observation}\n" + Style.RESET_ALL)
        print(Fore.MAGENTA + f"Query category: {category}" + Style.RESET_ALL)
        
        return {"current_interaction": state["current_interaction"].model_copy(update={
            "ai_response": f"Category: {category}",
            "observation": observation
        })}

    def construct_rag_queries(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Designing RAG queries...\n" + Style.RESET_ALL)
        
        interaction = state["current_interaction"]
        question = interaction["student_question"] if isinstance(interaction, dict) else interaction.student_question
        
        rag_result = self.agents.design_rag_queries.invoke({"query": question})
        queries = rag_result.queries 
        observation = f"Generated {len(queries)} follow-up questions: {queries[:2]}..."
        print(Fore.GREEN + f"OBSERVATION: {observation}\n" + Style.RESET_ALL)
        
        if isinstance(interaction, dict):
            interaction.update({
                "recommendations": queries,
                "observation": observation
            })
            return {"current_interaction": interaction}
        else:
            return {"current_interaction": state["current_interaction"].model_copy(update={
                "recommendations": queries,
                "observation": observation
            })}

    def generate_ai_response(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Generating AI response...\n" + Style.RESET_ALL)

        interaction = state["current_interaction"]
        history = state["agent_messages"]
        rewrite_feedback = (state["rewrite_feedback"] or "").strip()
        prefs = state.get("user_preferences") or {}
        
        if isinstance(interaction, dict):
            previous_answer = (interaction.get("ai_response") or "").strip()
            coursework = interaction.get("current_coursework")
        else:
            previous_answer = (interaction.ai_response or "").strip()
            coursework = interaction.current_coursework

        coursework_context = ""
        if coursework:
            due = f" Due: {coursework.dueDate}." if hasattr(coursework, 'dueDate') and coursework.dueDate else ""
            coursework_context = f'RELEVANT COURSEWORK: {coursework.title}{due}COURSEWORK DESCRIPTION: {coursework.description}'
        
        pdf_context = self._retrieve_pdf_context(interaction)
        
        student_context = state.get("student_context", "")
        if student_context:
            student_context_str = f"\n\nSTUDENT INFORMATION (from memory):\n{student_context}"
        else:
            student_context_str = ""

        if isinstance(pdf_context, str) and len(pdf_context) > 12000:
            pdf_context = pdf_context[:12000] + "\n\n[PDF context truncated]"

        # Build a preferences-aware wrapper for the AI response prompt
        language = prefs.get("language") or "English"
        tone = prefs.get("tone") or "helpful"
        agent_name = prefs.get("name") or "your tutor"
        extra = prefs.get("preference") or ""

        extra_line = f"\n- Additional notes: {extra}" if extra else ""
        prefs_header = (
            "\n\nUSER PREFERENCES:\n"
            f"- Preferred language: {language}\n"
            f"- Preferred tone: {tone}\n"
            f"- Agent name: {agent_name}" 
            f"{extra_line}\n"
        )

        if isinstance(interaction, dict):
            current_course = interaction.get("current_course")
            course_name = current_course.name if current_course else "N/A"
            student_question = interaction.get("student_question", "")
            recommendations = interaction.get("recommendations", [])
        else:
            course_name = interaction.current_course.name if interaction.current_course else "N/A"
            student_question = interaction.student_question
            recommendations = interaction.recommendations

        inputs = AI_RESPONSE_PROMPT.format(
            course_name=course_name,
            student_question=student_question,
            coursework_context=coursework_context,
            pdf_context=pdf_context + student_context_str + prefs_header,
            guidance=", ".join(recommendations)
        )
        
        if rewrite_feedback:
            inputs += f'REVISION INSTRUCTIONS: {rewrite_feedback}PREVIOUS ANSWER (FOR REVISION): {previous_answer}'
        
        ai_result = self.agents.ai_response_generator.invoke({"query_information": inputs, "history": history})
        response_text = ai_result.response if hasattr(ai_result, 'response') else ai_result.get('response', '')
        observation = f"Generated {len(response_text)} char response covering the student's question."
        print(Fore.GREEN + f"OBSERVATION: {observation}\n" + Style.RESET_ALL)
        
        if isinstance(interaction, dict):
            interaction.update({
                "ai_response": response_text,
                "observation": observation
            })
            return {
                "current_interaction": interaction,
                "rewrite_feedback": ""
            }
        else:
            return {
                "current_interaction": interaction.model_copy(update={
                    "ai_response": response_text,
                    "observation": observation
                }), 
                "rewrite_feedback": ""
            }
    
    def _retrieve_pdf_context(self, interaction) -> str:
        """Retrieves relevant PDF chunks (text/table/image summaries) from the vector store."""
        try:
            if isinstance(interaction, dict):
                current_course = interaction.get("current_course")
                student_question = interaction.get("student_question", "")
                recommendations = interaction.get("recommendations", [])
            else:
                current_course = interaction.current_course
                student_question = interaction.student_question
                recommendations = interaction.recommendations
            
            course_id = current_course.id if current_course else None
            if not course_id:
                return ""
            
            query = f"{student_question} {' '.join(recommendations[:2])}"
            retriever = self.pdf_processor.get_retriever(k=6, filter_dict={"course_id": course_id}, use_mmr=True)
            
            results = retriever.invoke(query)
            
            if not results:
                print(Fore.YELLOW + "No results with course filter, searching all courses..." + Style.RESET_ALL)
                retriever = self.pdf_processor.get_retriever(k=8, use_mmr=True)
                results = retriever.invoke(query)
            
            if results:
                print(Fore.CYAN + f"Retrieved {len(results)} relevant content items (text/tables/images):" + Style.RESET_ALL)
                pdf_texts = []
                max_chars = 10000
                current_chars = 0
                
                for item in results:
                    if isinstance(item, str):
                        preview = item[:150].replace('\n', ' ')
                        print(Fore.GREEN + f"  • Content: {preview}..." + Style.RESET_ALL)
                        if current_chars < max_chars:
                            take = item[: max(0, max_chars - current_chars)]
                            pdf_texts.append(take)
                            current_chars += len(take)
                    else:
                        content = getattr(item, 'page_content', str(item))
                        preview = content[:150].replace('\n', ' ')
                        print(Fore.GREEN + f"  • Content: {preview}..." + Style.RESET_ALL)
                        if current_chars < max_chars:
                            take = content[: max(0, max_chars - current_chars)]
                            pdf_texts.append(take)
                            current_chars += len(take)
                
                suffix = ""
                if current_chars >= max_chars:
                    suffix = "\n\n[PDF context truncated]"
                return "\n\nRELEVANT PDF CONTENT (includes text, tables, and image descriptions):\n" + "\n\n".join(pdf_texts) + suffix
            else:
                return ""
        except Exception as e:
            print(Fore.YELLOW + f"Could not retrieve PDF content: {str(e)}" + Style.RESET_ALL)
            return ""

    def verify_ai_response(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Verifying AI response...\n" + Style.RESET_ALL)
        
        interaction = state["current_interaction"]
        
        if isinstance(interaction, dict):
            student_question = interaction.get("student_question", "")
            ai_response = interaction.get("ai_response", "")
        else:
            student_question = interaction.student_question
            ai_response = interaction.ai_response
        
        review = self.agents.response_proofreader.invoke({
            "student_question": student_question,
            "ai_response": ai_response
        })
        
        observation = f"Quality check: {'PASSED - ready to send' if review.send else 'FAILED - needs revision'}. Feedback: {review.feedback[:80]}..."
        print(Fore.GREEN + f"OBSERVATION: {observation}\n" + Style.RESET_ALL)

        if isinstance(interaction, dict):
            if review.send:
                interaction.update({
                    "ai_response": ai_response + f"Feedback: {review.feedback}",
                    "observation": observation
                })
                return {
                    "current_interaction": interaction,
                    "sendable": True,
                    "rewrite_feedback": ""
                }

            trials = int(state.get("trials", 0)) + 1
            interaction.update({
                "observation": observation + f" Trial {trials}."
            })
            return {
                "current_interaction": interaction,
                "rewrite_feedback": review.feedback,
                "trials": trials
            }
        else:
            if review.send:
                return {
                    "current_interaction": interaction.model_copy(update={
                        "ai_response": ai_response + f"Feedback: {review.feedback}",
                        "observation": observation
                    }),
                    "sendable": True,
                    "rewrite_feedback": ""
                }

            trials = int(state.get("trials", 0)) + 1
            return {
                "current_interaction": interaction.model_copy(update={
                    "observation": observation + f" Trial {trials}."
                }),
                "sendable": False,
                "trials": trials,
                "rewrite_feedback": review.feedback
            }

    def finalize_response(self, state: GraphState) -> str:
        if state.get("sendable", False):
            print(Fore.GREEN + "AI response is ready to be sent to the student!" + Style.RESET_ALL)
            return "end"
        
        trials = int(state.get("trials", 0))
        max_trials = int(state.get("max_trials", 3))
        
        if trials >= max_trials:
            print(Fore.RED + "Max rewrite attempts reached; returning best-effort response." + Style.RESET_ALL)
            return "end"

        print(Fore.RED + "AI response needs improvement, rewriting..." + Style.RESET_ALL)
        return "rewrite"

    def reset_interaction(self) -> GraphState:
        return {"current_interaction": StudentInteraction()}


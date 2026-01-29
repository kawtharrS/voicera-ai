from colorama import Fore, Style
from ..model import Model 
from .agent import Agent
from .state import GraphState, Coursework, CourseWorkMaterial, StudentInteraction, Course
from tools.classroomTools import ClassroomTool
from tools.pdf_processor import PDFProcessor
from prompts.classroom import AI_RESPONSE_PROMPT
from ..shared_memory import shared_memory

model = Model()

class ClassroomNodes:
    def __init__(self):
        self.agents = Agent()
        self.classroom_tools = ClassroomTool()
        self.pdf_processor = PDFProcessor(self.classroom_tools)

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
            coursework_list = self.classroom_tools.list_coursework(course.id)
            all_coursework.extend(coursework_list)

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
        selected_coursework = state.get("courseworks", [None])[0]
            
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
        
        pdf_context = self.retrieve_pdf_context(interaction)
        
        student_context = state.get("student_context", "")
        if student_context:
            student_context_str = f"\n\nSTUDENT INFORMATION (from memory):\n{student_context}"
        else:
            student_context_str = ""

        if isinstance(pdf_context, str) and len(pdf_context) > 12000:
            pdf_context = pdf_context[:12000] + "\n\n[PDF context truncated]"

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
        
        if state.get("is_first_message"):
            response_text = f"Hi, I'm Eureka! {response_text}"
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
    
    def retrieve_pdf_context(self, interaction) -> str:
        """Retrieves relevant PDF chunks (text/table/image summaries) from the vector store."""
        try:
            if isinstance(interaction, dict):
                current_course = interaction.get("current_course")
                student_question = interaction.get("student_question", "")
            else:
                current_course = interaction.current_course
                student_question = interaction.student_question
            
            course_id = current_course.id if current_course else None
            if not course_id:
                return ""
            
            query = student_question
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
                    content = item if isinstance(item, str) else getattr(item, 'page_content', str(item))
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
                    "ai_response": ai_response,
                    "observation": f"{observation} Feedback: {review.feedback}"
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
                        "ai_response": ai_response,
                        "observation": f"{observation} Feedback: {review.feedback}"
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

    async def retrieve_memory(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Retrieving long-term memory..." + Style.RESET_ALL)
        student_id = state.get("student_id")
        if not student_id:
            return {"student_context": ""}
        
        memory = await shared_memory.retrieve(student_id)
        return {"student_context": memory}

    async def save_to_memory(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Saving interaction to long-term memory..." + Style.RESET_ALL)
        interaction = state.get("current_interaction")
        student_id = state.get("student_id")
        category = state.get("query_category") or "study"
        
        if not student_id or not interaction:
            return state

        if isinstance(interaction, dict):
            query = interaction.get("student_question", "")
            ai_response = interaction.get("ai_response", "")
        else:
            query = interaction.student_question
            ai_response = interaction.ai_response

        emotion = state.get("emotion") or ""
        
        await shared_memory.extract_and_save(
            query=query,
            ai_response=ai_response,
            user_id=student_id,
            category=category,
            emotion=emotion
        )
        return state

    def generate_study_plan(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Extracting study plan from response..." + Style.RESET_ALL)
        
        interaction = state["current_interaction"]
        if isinstance(interaction, dict):
            ai_response = interaction.get("ai_response", "")
        else:
            ai_response = interaction.ai_response
        
        if not ai_response:
            print(Fore.YELLOW + "No AI response to extract study plan from" + Style.RESET_ALL)
            return {"study_plan": None}
        
        try:
            result = self.agents.extract_study_slots.invoke({"ai_response": ai_response})
            
            if not result or not hasattr(result, 'slots') or not result.slots:
                print(Fore.YELLOW + "No study slots could be extracted from the response" + Style.RESET_ALL)
                return {"study_plan": None}
            
            valid_slots = []
            for slot in result.slots:
                if all(hasattr(slot, attr) for attr in ['day', 'start_time', 'end_time', 'activity']):
                    valid_slots.append(slot)
            
            if not valid_slots:
                print(Fore.YELLOW + "Study slots extracted but none are valid" + Style.RESET_ALL)
                return {"study_plan": None}
            
            print(Fore.GREEN + f"Extracted study plan with {len(valid_slots)} time slots" + Style.RESET_ALL)
            for slot in valid_slots[:5]:
                print(Fore.CYAN + f"  • {slot.day} {slot.start_time}-{slot.end_time}: {slot.activity}" + Style.RESET_ALL)
            
            from .structure_output import StudyPlanOutput
            return {"study_plan": StudyPlanOutput(slots=valid_slots)}
        except Exception as e:
            print(Fore.RED + f"Study plan extraction failed: {e}" + Style.RESET_ALL)
            import traceback
            traceback.print_exc()
            return {"study_plan": None}


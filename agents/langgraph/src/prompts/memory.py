FACT_EXTRACTION_PROMPT = """
Analyze the following user query and extract any important personal facts, 
preferences, or context that should be remembered for future interactions.
If there are no new important facts, return "NO FACTS".

User Query: {query}

Return ONLY the extracted facts or "NO FACTS".
"""
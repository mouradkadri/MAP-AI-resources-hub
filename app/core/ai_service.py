import google.generativeai as genai
import json
import time
import gc

class AIService:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def extract_resource(self, chunk, tagging_guide):
        prompt = f"""
        You are an expert data miner. Find EVERY resource/tool with a valid URL.
        
        {tagging_guide}

        **INSTRUCTIONS:**
        1. Extract: title, provider, description, link.
        2. Categorize using the "OFFICIAL TAGGING DICTIONARY".
        3. Output: Strictly formatted JSON LIST of objects.

        **Text:**
        '''
        {chunk}
        '''
        """
        retries = 3
        delay = 2
        for i in range(retries):
            try:
                gc.collect()
                response = self.model.generate_content(prompt)
                
                # --- SAFETY FIX STARTS HERE ---
                
                # 1. Check if response object exists
                if not response: 
                    return []

                # 2. Safely get text (Handles blocked responses)
                try:
                    raw_text = response.text
                except Exception:
                    # If AI safety filter blocks it, .text raises an error
                    print(f"      [AI] Chunk blocked by safety filters.")
                    return []

                # 3. Check if text is None before stripping
                if raw_text is None:
                    return []

                # 4. Now safe to strip
                cleaned = raw_text.strip().replace("```json", "").replace("```", "").strip()
                
                # --- SAFETY FIX ENDS HERE ---

                if not cleaned: return []
                
                try:
                    data = json.loads(cleaned)
                    if isinstance(data, dict): return [data]
                    if isinstance(data, list): return data
                    return []
                except json.JSONDecodeError:
                    # Sometimes AI returns text instead of JSON. Retry.
                    continue

            except Exception as e:
                # print(f"AI Error: {e}")
                time.sleep(delay)
                delay *= 2
        
        return []
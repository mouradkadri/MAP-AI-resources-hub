import os
import uuid
import gc
import re
import traceback
from datetime import datetime

from app.config import AppConfig
from app.core.content_streamer import ContentStreamer
from app.core.ai_service import AIService
from app.core.data_handler import DataHandler

def main(stop_event=None):
    print("--- AI Resource Tagger (CSV Mode - Active) ---")
    
    try:
        config = AppConfig.load_settings()
        api_key = config['API'].get('GEMINI_API_KEY')
        if not api_key:
            print("❌ Error: Missing Gemini API Key.")
            return

        ai = AIService(api_key)
        
        hist_file = os.path.join(AppConfig.BASE_DIR, "processed_history.log")
        tag_file = os.path.join(AppConfig.BASE_DIR, "tagging_reference.csv")
        
        guide = DataHandler.load_tagging_guide(tag_file)
        full_map = DataHandler.load_category_map(tag_file)
        
        history = DataHandler.load_history(hist_file)
        existing_data = DataHandler.load_data() 
        processed_links = {row.get('link', '').strip() for row in existing_data if row.get('link')}
        
        if not os.path.exists(AppConfig.RESOURCES_DIR):
            print(f"❌ Resources folder missing.")
            return

        files = [f for f in os.listdir(AppConfig.RESOURCES_DIR) 
                 if f.lower().endswith(('.pdf', '.docx', '.txt'))]
        
        count = 0
        skipped_history = 0

        for i, filename in enumerate(files):
            if stop_event and stop_event.is_set(): break
            
            if filename in history: 
                skipped_history += 1
                continue 

            print(f"[{i+1}/{len(files)}] Scanning: {filename}...")
            file_path = os.path.join(AppConfig.RESOURCES_DIR, filename)
            file_links = set()

            try:
                stream = ContentStreamer.generator(file_path, os.path.splitext(filename)[1].lower())
                
                if stream:
                    for chunk in stream:
                        if stop_event and stop_event.is_set(): break
                        
                        results = ai.extract_resource(chunk, guide)
                        if not results: continue

                        for item in results:
                            if not isinstance(item, dict): continue

                            def safe_str(val):
                                if val is None: return ""
                                return str(val).strip()

                            link = safe_str(item.get('link'))
                            if not link or link in processed_links or link in file_links: continue

                            # --- TAG MERGING & MAPPING ---
                            raw_tags = item.get('tags')
                            raw_tech = item.get('tech_tags')
                            
                            all_found = []
                            def extract(val):
                                if isinstance(val, list):
                                    for v in val:
                                        if isinstance(v, dict):
                                            if 'tag' in v: all_found.append(str(v['tag']))
                                            elif 'hashtag' in v: all_found.append(str(v['hashtag']))
                                        else: all_found.append(str(v))
                                elif isinstance(val, str):
                                    # Clean strings
                                    clean = val.replace("['", "").replace("']", "").replace("'", "").replace('"', "")
                                    for t in clean.split(','):
                                        if t.strip(): all_found.append(t.strip())

                            extract(raw_tags)
                            extract(raw_tech)
                            all_found = list(set(all_found))

                            forced_cat = ""
                            forced_sub = ""

                            # Check Map
                            for t in all_found:
                                clean_t = t.strip()
                                lower_t = clean_t.lower()
                                match = full_map.get(lower_t) or full_map.get("#"+lower_t)

                                if match:
                                    if not forced_cat:
                                        forced_cat = match['group']
                                        forced_sub = match['sub']

                            tags_db = ", ".join(all_found)

                            # Fallback if map fail
                            if not forced_cat: forced_cat = safe_str(item.get('category'))
                            if not forced_sub: forced_sub = safe_str(item.get('subcategory'))

                            row = {
                                'id': str(uuid.uuid4()),
                                'created_at': datetime.utcnow().isoformat(),
                                'title': safe_str(item.get('title')) or 'Unknown',
                                'provider': safe_str(item.get('provider')),
                                'votes': 0, 'level': '',
                                'description': safe_str(item.get('description')),
                                'category': forced_cat,
                                'outcomes': '', 'link': link, 'approved': False, 
                                'image': '', 
                                'tags': tags_db,
                                'subcategory': forced_sub
                            }

                            if DataHandler.append_csv_safe(AppConfig.CSV_FILE, fieldnames=['id', 'created_at', 'title', 'provider', 'votes', 'level', 'description', 'category', 'outcomes', 'link', 'approved', 'image', 'tags', 'tech_tags', 'subcategory'], row_data=row):
                                processed_links.add(link)
                                file_links.add(link)
                                count += 1
                                print(f"   + Added: {row['title']} (Sub: {forced_sub})")

                if not (stop_event and stop_event.is_set()):
                    DataHandler.mark_history(hist_file, filename)
            
            except Exception as e:
                print(f"❌ Error in {filename}: {e}")
            
            gc.collect()

        if count == 0:
            print("\n✅ Scan Complete. No new resources.")
        else:
            print(f"\n✅ Job Complete. Added {count} new resources.")

    except Exception as e:
        print(f"❌ SCRIPT ERROR: {e}")
        traceback.print_exc()
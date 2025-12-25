import os
import uuid
import gc
import re
import traceback
from datetime import datetime
from supabase import create_client

from app.config import AppConfig
from app.core.content_streamer import ContentStreamer
from app.core.ai_service import AIService
from app.core.data_handler import DataHandler

def main(stop_event=None):
    print("--- AI Resource Uploader (Database Mode - Active) ---")

    config = AppConfig.load_settings()
    try:
        api_key = config['API']['GEMINI_API_KEY']
        sup_url = config['SETTINGS']['SUPABASE_URL']
        sup_key = config['API']['SUPABASE_KEY']
    except KeyError:
        print("❌ Error: Missing API Keys.")
        return

    ai = AIService(api_key)
    
    try:
        supabase = create_client(sup_url, sup_key)
        print("✅ Connected to Supabase.")
    except Exception as e:
        print(f"❌ Supabase Connection Failed: {e}")
        return

    hist_file = os.path.join(AppConfig.BASE_DIR, "processed_history.log")
    tag_file = os.path.join(AppConfig.BASE_DIR, "tagging_reference.csv")
    
    guide = DataHandler.load_tagging_guide(tag_file)
    full_map = DataHandler.load_category_map(tag_file)
    history = DataHandler.load_history(hist_file)
    
    try:
        res = supabase.table('requested_resources').select('link').execute()
        db_links = {row['link'].strip() for row in res.data if row.get('link')}
        print(f"ℹ️  {len(db_links)} links in DB.")
    except:
        db_links = set()

    if not os.path.exists(AppConfig.RESOURCES_DIR):
        print(f"❌ Resources folder not found.")
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
                        if not link or link in db_links or link in file_links: continue

                        # --- TAG MERGING ---
                        all_found = []
                        def extract(val):
                            if isinstance(val, list):
                                for v in val:
                                    if isinstance(v, dict):
                                        if 'tag' in v: all_found.append(str(v['tag']))
                                        elif 'hashtag' in v: all_found.append(str(v['hashtag']))
                                    else: all_found.append(str(v))
                            elif isinstance(val, str):
                                found = re.findall(r"#\w+", val)
                                if not found and val.strip(): found = [val.strip()]
                                all_found.extend(found)

                        extract(item.get('tags'))
                        extract(item.get('tech_tags'))
                        all_found = list(set(all_found))

                        forced_cat = ""
                        forced_sub = ""

                        for t in all_found:
                            clean_t = t.strip()
                            lower_t = clean_t.lower()
                            match = full_map.get(lower_t) or full_map.get("#"+lower_t)

                            if match:
                                if not forced_cat:
                                    forced_cat = match['group']
                                    forced_sub = match['sub']

                        tags_db = ", ".join(all_found)

                        # Fallbacks
                        if not forced_cat: forced_cat = safe_str(item.get('category'))
                        if not forced_sub: forced_sub = safe_str(item.get('subcategory'))

                        # --- ROW ---
                        row = {
                            'id': str(uuid.uuid4()),
                            'created_at': datetime.utcnow().isoformat(),
                            'title': safe_str(item.get('title')) or 'Unknown',
                            'provider': safe_str(item.get('provider')),
                            'votes': 0, 'level': 'Beginner',
                            'description': safe_str(item.get('description')),
                            'category': forced_cat,
                            'outcomes': '', 'link': link, 'approved': False, 
                            'image': '', 
                            'tags': tags_db,
                            'tech_tags': '', 
                            'subcategory': forced_sub
                        }

                        try:
                            res = supabase.table('requested_resources').insert(row).execute()
                            if res.data:
                                db_links.add(link)
                                file_links.add(link)
                                count += 1
                                print(f"   ☁️  Uploaded: {row['title']} (Sub: {forced_sub})")
                        except Exception as e:
                            print(f"   ❌ DB Insert Error: {e}")

            if not (stop_event and stop_event.is_set()):
                DataHandler.mark_history(hist_file, filename)
        
        except Exception as e:
            print(f"❌ Error in {filename}: {e}")
        
        gc.collect()

    if skipped_history > 0:
        print(f"ℹ️  Skipped {skipped_history} files.")
    print(f"\n✅ Job Complete. Uploaded {count} new resources.")
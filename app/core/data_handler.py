import csv
import os
import shutil
import time
from app.config import AppConfig

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

class DataHandler:
    
    # --- UI / GENERAL CSV METHODS ---
    @staticmethod
    def load_data():
        if not os.path.exists(AppConfig.CSV_FILE): return []
        try:
            with open(AppConfig.CSV_FILE, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        except: return []

    @staticmethod
    def update_cell(row_idx, col_name, new_val):
        if not os.path.exists(AppConfig.CSV_FILE): return
        try:
            rows = []
            with open(AppConfig.CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                rows = list(reader)
            if 0 <= row_idx < len(rows):
                rows[row_idx][col_name] = new_val
                with open(AppConfig.CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
        except: pass

    @staticmethod
    def export_data(destination_path):
        if not os.path.exists(AppConfig.CSV_FILE): return False
        try:
            shutil.copy(AppConfig.CSV_FILE, destination_path)
            return True
        except: return False

    # --- WORKER / LOGIC METHODS ---

    @staticmethod
    def load_tagging_guide(csv_path):
        return DataHandler._read_ref_file(csv_path, mode='text', verbose=True)

    @staticmethod
    def load_category_map(csv_path):
        """Returns { '#hashtag': {'group': '...', 'sub': '...'} }"""
        return DataHandler._read_ref_file(csv_path, mode='dict', verbose=False)

    @staticmethod
    def _read_ref_file(csv_path, mode='text', verbose=True):
        if not os.path.exists(csv_path): 
            print(f"⚠️ Reference file not found: {csv_path}")
            return "" if mode == 'text' else {}
        
        guide_text = "--- OFFICIAL TAGGING DICTIONARY ---\n"
        full_map = {} 
        
        def process_row(tag, group, sub, defn):
            tag = str(tag).strip()
            # Clean weird chars
            if not tag or tag.lower() == 'nan': return

            group = str(group).strip()
            
            # Clean Subcategory
            sub = str(sub).strip()
            if sub.lower() == 'nan': sub = ""
            
            defn = str(defn).strip()
            
            # Map Logic
            entry = {'group': group, 'sub': sub}
            full_map[tag.lower()] = entry
            
            # Store both "#tag" and "tag" for safe matching
            if not tag.startswith("#"):
                full_map["#" + tag.lower()] = entry
            else:
                full_map[tag.replace("#", "").lower()] = entry
            
            # Text Logic
            if mode == 'text':
                nonlocal guide_text
                guide_text += f"Tag: {tag}, Group: {group}, Sub: {sub}, Def: {defn}\n"

        # --- STRATEGY 1: PANDAS (Best for .xlsx and mixed CSVs) ---
        if HAS_PANDAS:
            try:
                # 1. Try Semicolon first (Specific for your file)
                try:
                    df = pd.read_csv(csv_path, sep=';', on_bad_lines='skip', encoding='utf-8')
                    if len(df.columns) < 2: raise Exception("Wrong separator")
                except:
                    # 2. Fallback to Comma
                    try:
                        df = pd.read_csv(csv_path, sep=',', on_bad_lines='skip', encoding='utf-8')
                    except:
                        # 3. Fallback to Excel
                        df = pd.read_excel(csv_path)

                df.columns = df.columns.astype(str).str.strip().str.lower()
                
                # Dynamic Column Finder
                tag_c = next((c for c in df.columns if c in ['hashtag', 'tag']), None)
                grp_c = next((c for c in df.columns if 'primary group' in c or 'group' in c), None)
                sub_c = next((c for c in df.columns if 'Subcategory' in c or 'sub' in c), None)
                def_c = next((c for c in df.columns if 'definition' in c), None)

                if tag_c:
                    count = 0
                    for _, row in df.iterrows():
                        process_row(
                            row[tag_c], 
                            row[grp_c] if grp_c else "",
                            row[sub_c] if sub_c else "",
                            row[def_c] if def_c else ""
                        )
                        count += 1
                    
                    if verbose and mode=='text' and count > 0: 
                        print(f"✅ Reference loaded ({count} tags).")
                    return guide_text if mode == 'text' else full_map

            except Exception as e:
                print(f"⚠️ Pandas read error: {e}")

        # --- STRATEGY 2: RAW TEXT (Fallback) ---
        # Specifically updated to handle your Semicolon format
        try:
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    
                    # Detect delimiter
                    delim = ';' if ';' in line else ','
                    parts = line.split(delim)
                    
                    # Ensure we have at least Tag and Group
                    if len(parts) > 1:
                        # Index 0: Tag
                        t = parts[0].strip().replace('"', '')
                        if t.startswith("#"):
                            # Index 1: Group
                            g = parts[1].strip().replace('"', '')
                            
                            # Index 2: Subcategory (Crucial Fix)
                            s = ""
                            if len(parts) > 2:
                                s = parts[2].strip().replace('"', '')
                            
                            # Index 3: Definition
                            d = ""
                            if len(parts) > 3:
                                d = parts[3].strip().replace('"', '')
                                
                            process_row(t, g, s, d)
                            
            return guide_text if mode == 'text' else full_map
        except:
            return "" if mode == 'text' else {}

    @staticmethod
    def load_history(history_path):
        if not os.path.exists(history_path): return set()
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        except: return set()

    @staticmethod
    def mark_history(history_path, filename):
        try:
            with open(history_path, 'a', encoding='utf-8') as f:
                f.write(f"{filename}\n")
        except: pass

    @staticmethod
    def append_csv_safe(file_path, fieldnames, row_data):
        retries = 3
        while retries > 0:
            try:
                file_exists = os.path.exists(file_path) and os.path.getsize(file_path) > 0
                with open(file_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    if not file_exists: writer.writeheader()
                    writer.writerow(row_data)
                return True
            except PermissionError:
                time.sleep(1)
                retries -= 1
            except: return False
        return False
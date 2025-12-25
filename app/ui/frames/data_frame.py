import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from app.core.data_handler import DataHandler

class DataFrame(ctk.CTkFrame):
    def __init__(self, parent, main_controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = main_controller
        self.setup_ui()

    def setup_ui(self):
        # Toolbar
        tool_dat = ctk.CTkFrame(self, fg_color="transparent")
        tool_dat.pack(fill="x", pady=5)
        ctk.CTkLabel(tool_dat, text="Double-click cells to edit", text_color="gray").pack(side="left")
        ctk.CTkButton(tool_dat, text="Save/Export CSV", command=self.export_csv, fg_color="#2b825b", width=120).pack(side="right", padx=5)
        ctk.CTkButton(tool_dat, text="Refresh", command=self.refresh_data, width=80, fg_color="#333").pack(side="right")

        # Treeview
        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        # --- COLUMNS DEFINITION ---
        self.columns = ('title', 'provider', 'category', 'subcategory', 'tags', 'link')
        
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show='headings')
        
        # Scrollbars
        ys = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        xs = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        
        ys.pack(side="right", fill="y")
        xs.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # --- HEADERS ---
        headers = ['Title', 'Provider', 'Category', 'Subcategory', 'Tags', 'Link']
        widths = [200, 100, 120, 120, 200, 200]
        
        for col, h, w in zip(self.columns, headers, widths):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=w)

        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_data(self):
        # Clear existing
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        
        data = DataHandler.load_data()
        
        for row in data:
            # Helper to find keys case-insensitively
            def get_val(keys):
                for k in keys:
                    if k in row and row[k]:
                        return str(row[k]) # Ensure string
                return ""

            title = get_val(['title', 'Title'])
            provider = get_val(['provider', 'Provider'])
            category = get_val(['category', 'Category', 'primary group', 'Group'])
            
            # --- NEW: SUBCATEGORY ---
            subcategory = get_val(['subcategory', 'Subcategory', 'sub'])

            # Tags: Combine tech_tags + tags, clean list characters
            raw_t1 = get_val(['tech_tags', 'Tech_Tags'])
            raw_t2 = get_val(['tags', 'Tags'])
            combined = (raw_t1 + "," + raw_t2).replace("['", "").replace("']", "").replace('"', "").replace("'", "")
            
            # Clean split
            clean_tags_list = [t.strip() for t in combined.split(',') if t.strip()]
            display_tags = ", ".join(clean_tags_list)

            # Fallback Logic: If Category is empty, try to fill from tags?
            # (Optional: Removed here to respect the strict logic from worker script)

            link = get_val(['link', 'Link', 'url', 'URL'])

            vals = [title, provider, category, subcategory, display_tags, link]
            self.tree.insert("", "end", values=vals)
            
        return len(data)

    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return
        
        col_id = self.tree.identify_column(event.x)
        item_id = self.tree.focus()
        
        # Convert column ID (#1, #2) to index (0, 1)
        col_idx = int(col_id.replace("#", "")) - 1
        
        x, y, w, h = self.tree.bbox(item_id, col_id)
        current_values = self.tree.item(item_id).get("values")
        if not current_values: return
        
        curr_val = current_values[col_idx]

        entry = tk.Entry(self.tree, width=w, bg="#333", fg="white")
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, curr_val)
        entry.focus()

        def save(e):
            new_val = entry.get()
            
            # Update UI
            vals = list(self.tree.item(item_id).get("values"))
            vals[col_idx] = new_val
            self.tree.item(item_id, values=vals)
            entry.destroy()
            
            # Map visual column index back to CSV Column Name
            # Columns: title, provider, category, subcategory, tags, link
            csv_map = ['title', 'provider', 'category', 'subcategory', 'tags', 'link']
            
            if 0 <= col_idx < len(csv_map):
                col_name = csv_map[col_idx]
                row_idx = self.tree.index(item_id)
                
                # If editing tags here, we save to 'tags' column 
                # (tech_tags is treated as merged/read-only or hidden backend field)
                DataHandler.update_cell(row_idx, col_name, new_val)
                self.controller.update_analytics_if_needed()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def export_csv(self):
        dest = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if dest:
            if DataHandler.export_data(dest):
                messagebox.showinfo("Success", "Export successful.")
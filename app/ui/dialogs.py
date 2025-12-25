import customtkinter as ctk
import configparser
from tkinter import messagebox

class Splash(ctk.CTkToplevel):
    def __init__(self, parent, version, callback):
        super().__init__(parent)
        self.callback = callback
        self.overrideredirect(True)
        
        # Center Window
        w, h = 500, 300
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        
        frame = ctk.CTkFrame(self, corner_radius=20, fg_color="#1a1a1a", border_width=2, border_color="#333")
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(frame, text="AI INTELLIGENCE", font=("Roboto Medium", 28), text_color="white").pack(pady=(70, 5))
        ctk.CTkLabel(frame, text="RESOURCE MANAGEMENT SYSTEM", font=("Roboto", 10, "bold"), text_color="#3B8ED0").pack(pady=(0, 30))
        
        prog = ctk.CTkProgressBar(frame, width=250, mode="indeterminate")
        prog.pack(pady=10)
        prog.start()
        
        ctk.CTkLabel(frame, text=f"Initializing {version}...", font=("Consolas", 10), text_color="#666").pack(side="bottom", pady=20)
        
        self.after(2500, self.close)

    def close(self):
        self.destroy()
        self.callback()

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config_path):
        super().__init__(parent)
        self.config_path = config_path
        self.title("Configuration")
        self.geometry("500x450")
        self.grab_set()
        self.setup_ui()

    def setup_ui(self):
        config = configparser.ConfigParser()
        config.read(self.config_path)
        
        ctk.CTkLabel(self, text="Settings & API Keys", font=("Roboto Medium", 18)).pack(pady=20)
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(padx=30, fill="x")

        self.e_gemini = self.create_entry(form, "Gemini API Key", config.get('API', 'GEMINI_API_KEY', fallback=""), True)
        self.e_sup_url = self.create_entry(form, "Supabase URL", config.get('SETTINGS', 'SUPABASE_URL', fallback=""))
        self.e_sup_key = self.create_entry(form, "Supabase Service Key", config.get('API', 'SUPABASE_KEY', fallback=""), True)

        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(pady=30)
        ctk.CTkButton(btn_box, text="Save Settings", command=self.save, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_box, text="Cancel", command=self.destroy, width=120, fg_color="transparent", border_width=1).pack(side="left", padx=10)

    def create_entry(self, parent, lbl, default, is_pass=False):
        ctk.CTkLabel(parent, text=lbl, anchor="w", text_color="#aaa").pack(fill="x", pady=(10,0))
        entry = ctk.CTkEntry(parent, placeholder_text="Enter value...", show="•" if is_pass else "")
        entry.pack(fill="x", pady=5)
        entry.insert(0, default)
        return entry

    def save(self):
        config = configparser.ConfigParser()
        config['API'] = {'GEMINI_API_KEY': self.e_gemini.get().strip(), 'SUPABASE_KEY': self.e_sup_key.get().strip()}
        config['SETTINGS'] = {'SUPABASE_URL': self.e_sup_url.get().strip()}
        
        with open(self.config_path, 'w') as f: config.write(f)
        messagebox.showinfo("Saved", "Configuration updated successfully.")
        self.destroy()
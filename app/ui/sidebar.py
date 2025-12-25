import customtkinter as ctk
import datetime

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_open_folder, on_db, on_csv, on_cancel, version):
        super().__init__(parent, width=220, corner_radius=0)
        self.grid_rowconfigure(10, weight=1)
        
        # Title
        ctk.CTkLabel(self, text="AI RESOURCE\nHUB", font=("Roboto", 20, "bold")).pack(pady=(40,5), padx=20, anchor="w")
        ctk.CTkLabel(self, text="OPERATIONS CENTER", font=("Roboto", 10, "bold"), text_color="#3B8ED0").pack(anchor="w", padx=20)
        
        # Config Status
        self.lbl_config = ctk.CTkLabel(self, text="⚫ System Ready", font=("Roboto", 11), text_color="gray")
        self.lbl_config.pack(padx=20, pady=(10, 20), anchor="w")

        # Buttons
        self.btn_open = self.create_btn("📂  Open Folder", on_open_folder)
        ctk.CTkFrame(self, height=2, fg_color="#333").pack(fill="x", padx=20, pady=15)
        
        self.btn_db = self.create_btn("🚀  Upload to DB", on_db)
        self.btn_csv = self.create_btn("📊  Export Excel", on_csv)
        
        # Cancel Button (Hidden by default)
        self.btn_cancel = ctk.CTkButton(self, text="CANCEL JOB", fg_color="#cf3434", hover_color="#8a2323", 
                                        height=40, font=("Roboto", 12, "bold"), command=on_cancel)
        
        # Bottom Info
        self.lbl_clock = ctk.CTkLabel(self, text="00:00", font=("Roboto", 28))
        self.lbl_clock.pack(side="bottom", anchor="w", padx=20, pady=(0, 5))
        ctk.CTkLabel(self, text=version, text_color="gray60", font=("Roboto", 10)).pack(side="bottom", anchor="w", padx=20, pady=10)

    def create_btn(self, text, cmd):
        btn = ctk.CTkButton(self, text=text, command=cmd, fg_color="transparent", text_color=("gray10", "gray90"),
                            hover_color=("gray70", "gray30"), anchor="w", height=40, font=("Roboto", 13))
        btn.pack(fill="x", padx=10, pady=4)
        return btn

    def set_working_state(self, is_working):
        state = "disabled" if is_working else "normal"
        self.btn_db.configure(state=state)
        self.btn_csv.configure(state=state)
        
        if is_working:
            self.btn_cancel.pack(padx=20, pady=20, fill="x")
        else:
            self.btn_cancel.pack_forget()

    def update_clock(self):
        self.lbl_clock.configure(text=datetime.datetime.now().strftime("%I:%M %p"))
import customtkinter as ctk
import tkinter as tk

class ConsoleFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.setup_ui()

    def setup_ui(self):
        # 1. Toolbar (Top)
        tool_con = ctk.CTkFrame(self, fg_color="transparent")
        tool_con.pack(fill="x", pady=5)
        
        ctk.CTkLabel(tool_con, text="Live Operation Logs", font=("Roboto", 12, "bold"), text_color="gray").pack(side="left")
        ctk.CTkButton(tool_con, text="Clear Log", width=80, height=25, fg_color="#333", hover_color="#444", 
                      command=self.clear_logs).pack(side="right")
        
        # 2. Progress Bar (Created but hidden initially)
        self.progress = ctk.CTkProgressBar(self, height=8, corner_radius=4)
        self.progress.set(0)

        # 3. Log Container (Bottom - stored as self.log_container for reference)
        self.log_container = ctk.CTkFrame(self, fg_color="transparent")
        self.log_container.pack(fill="both", expand=True, pady=10)
        
        # Scrollbar & Text
        log_scroll = ctk.CTkScrollbar(self.log_container, orientation="vertical")
        log_scroll.pack(side="right", fill="y")
        
        self.log_box = tk.Text(self.log_container, bg="#2b2b2b", fg="#e0e0e0", font=("Consolas", 12),
                               bd=0, highlightthickness=0, state="disabled", yscrollcommand=log_scroll.set)
        
        self.log_box.pack(side="left", fill="both", expand=True)
        log_scroll.configure(command=self.log_box.yview)

        # Tags
        self.log_box.tag_config("timestamp", foreground="#777777")
        self.log_box.tag_config("error", foreground="#ff5555")
        self.log_box.tag_config("success", foreground="#50fa7b")
        self.log_box.tag_config("warning", foreground="#ffb86c")
        self.log_box.tag_config("info", foreground="#8be9fd")

    def add_log(self, text, timestamp, tag):
        self.log_box.configure(state='normal')
        if timestamp:
            self.log_box.insert("end", timestamp, "timestamp")
        self.log_box.insert("end", text + "\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state='disabled')

    def clear_logs(self):
        self.log_box.configure(state='normal')
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state='disabled')

    def show_progress(self, show=True):
        if show:
            self.progress.pack(fill="x", padx=10, pady=(0,10), before=self.log_container)
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.pack_forget()
from tkinter import ttk

def setup_ttk_styles():
    style = ttk.Style()
    style.theme_use("clam")
    
    style.configure("Treeview",
                    background="#2b2b2b",
                    foreground="white",
                    fieldbackground="#2b2b2b",
                    borderwidth=0,
                    font=("Roboto", 10),
                    rowheight=30)
    
    style.configure("Treeview.Heading",
                    background="#1f1f1f",
                    foreground="white",
                    relief="flat",
                    font=("Roboto", 10, "bold"))
    
    style.map("Treeview", background=[('selected', '#1f538d')])
from app.ui.main_window import MainApp
from app.ui.styles import setup_ttk_styles
from tkinter import ttk

if __name__ == "__main__":
    app = MainApp()
    
    # We must setup TTK styles after the root window is created
    setup_ttk_styles()
    
    app.mainloop()
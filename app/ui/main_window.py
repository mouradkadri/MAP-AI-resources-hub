import customtkinter as ctk
import threading
import time
import os
import psutil

from app.config import AppConfig
from app.core.logger import ConsoleLogger
from app.ui.sidebar import Sidebar
from app.ui.dialogs import Splash, SettingsDialog
from app.ui.frames.console_frame import ConsoleFrame
from app.ui.frames.data_frame import DataFrame
from app.ui.frames.analytics_frame import AnalyticsFrame

# Try importing workers
try:
    from app.workers import script_db, script_csv
    SCRIPTS_AVAILABLE = True
except Exception as e:
    print(f"❌ DETAILED IMPORT ERROR: {e}")  
    import traceback
    traceback.print_exc()                    
    SCRIPTS_AVAILABLE = False

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Setup
        self.withdraw()
        self.title(AppConfig.APP_TITLE)
        self.geometry("1200x800")
        self.minsize(1000, 700)
        ctk.set_appearance_mode(AppConfig.THEME_MODE)
        ctk.set_default_color_theme(AppConfig.THEME_COLOR)
        
        try: self.iconbitmap(AppConfig.ICON_FILE)
        except: pass

        # Core Components
        self.logger = ConsoleLogger()
        self.logger.start_redirect()
        self.stop_event = threading.Event()

        # UI Construction
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.setup_sidebar()
        self.setup_main_area()
        
        # Splash
        self.splash = Splash(self, AppConfig.VERSION, self.finish_init)

    def finish_init(self):
        self.deiconify()
        self.check_log_queue()
        self.update_system_stats()
        self.update_clock()
        # Initial Data Load
        count = self.frame_data.refresh_data()
        self.lbl_count.configure(text=f"Records: {count}")
        self.frame_analytics.update_charts()

    def write(self, text):
        """Thread-safe write helper used by background threads.
        Proxies to the ConsoleLogger.write method when available so we avoid
        invoking nonexistent attributes on the Tk root from threads.
        """
        try:
            if hasattr(self, 'logger') and self.logger:
                # Use logger.write to capture caller stack and other metadata
                try:
                    self.logger.write(text)
                except Exception:
                    # Fallback: put raw text into queue
                    try:
                        self.logger.log_queue.put(str(text))
                    except Exception:
                        pass
            else:
                # Last resort: print directly to stdout
                print(text)
        except Exception:
            try:
                print(f"[MAINAPP WRITE ERROR] {repr(text)}")
            except Exception:
                pass

    def setup_sidebar(self):
        self.sidebar = Sidebar(self, 
                               on_open_folder=self.open_resources,
                               on_db=lambda: self.start_worker("db"),
                               on_csv=lambda: self.start_worker("csv"),
                               on_cancel=self.cancel_worker,
                               version=AppConfig.VERSION)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Top Bar
        top = ctk.CTkFrame(self.main_frame, height=60, corner_radius=0, fg_color=("white", "#212121"))
        top.pack(fill="x")
        ctk.CTkLabel(top, text="Dashboard & Analytics", font=("Roboto", 16, "bold")).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(top, text="⚙ Settings", width=80, command=self.open_settings, fg_color="#333").pack(side="right", padx=20)

        # Tabs
        self.tabs = ctk.CTkTabview(self.main_frame, corner_radius=15)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        self.tabs.add("Console")
        self.tabs.add("Data")
        self.tabs.add("Analytics")

        self.frame_console = ConsoleFrame(self.tabs.tab("Console"))
        self.frame_console.pack(fill="both", expand=True)

        self.frame_data = DataFrame(self.tabs.tab("Data"), self)
        self.frame_data.pack(fill="both", expand=True)

        self.frame_analytics = AnalyticsFrame(self.tabs.tab("Analytics"))
        self.frame_analytics.pack(fill="both", expand=True)

        # Footer
        footer = ctk.CTkFrame(self.main_frame, height=35, corner_radius=0, fg_color=("#f0f0f0", "#1a1a1a"))
        footer.pack(fill="x", side="bottom")
        self.lbl_status = ctk.CTkLabel(footer, text="Ready", font=("Roboto", 11), text_color="gray")
        self.lbl_status.pack(side="left", padx=20)
        
        self.lbl_stats = ctk.CTkLabel(footer, text="CPU: --%", font=("Consolas", 11), text_color="#3B8ED0")
        self.lbl_stats.pack(side="right", padx=20)
        self.lbl_count = ctk.CTkLabel(footer, text="Records: 0", font=("Roboto", 11, "bold"))
        self.lbl_count.pack(side="right", padx=10)

    # --- Actions ---
    def open_settings(self):
        SettingsDialog(self, AppConfig.CONFIG_FILE)

    def open_resources(self):
        if not os.path.exists(AppConfig.RESOURCES_DIR): os.makedirs(AppConfig.RESOURCES_DIR)
        os.startfile(AppConfig.RESOURCES_DIR)

    def update_analytics_if_needed(self):
        self.frame_analytics.update_charts()

    # --- Background Loops ---
    def check_log_queue(self):
        while not self.logger.log_queue.empty():
            text = self.logger.log_queue.get()

            # Filter out internal logger-only markers (keep UI clean)
            try:
                if isinstance(text, str) and text.startswith("[LOGGER"):
                    continue
            except Exception:
                pass

            ts, tag = self.logger.format_log(text)
            if ts:
                # Ensure we have a string for display and label updates
                try:
                    disp = text if isinstance(text, str) else str(text)
                except Exception:
                    disp = ""

                self.frame_console.add_log(disp, ts, tag)
                if disp:
                    try:
                        self.lbl_status.configure(text=f"Event: {disp.strip()[:60]}...")
                    except Exception:
                        pass

        self.after(300, self.check_log_queue)

    def update_system_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.lbl_stats.configure(text=f"CPU: {cpu}%  RAM: {ram}%")
        except: pass
        self.after(2000, self.update_system_stats)

    def update_clock(self):
        self.sidebar.update_clock()
        self.after(1000, self.update_clock)

    # --- Worker Thread Management ---
    def start_worker(self, mode):
        if not SCRIPTS_AVAILABLE:
            print("❌ Worker scripts not found in app/workers/")
            return

        self.frame_console.clear_logs()
        self.tabs.set("Console")
        self.stop_event.clear()
        self.sidebar.set_working_state(True)
        self.frame_console.show_progress(True)
        
        t = threading.Thread(target=self.run_process, args=(mode,))
        t.daemon = True
        t.start()

    def cancel_worker(self):
        self.stop_event.set()
        print("⚠ Initiating Cancel Sequence...")

    def run_process(self, mode):
        # ... (keep existing setup code) ...
        self.write(f"--- STARTING {mode.upper()} PROCESS ---")
        time.sleep(0.5)
        try:
            if mode == 'db':
                try: script_db.main(self.stop_event)
                except TypeError: script_db.main() 
            else:
                try: script_csv.main(self.stop_event)
                except TypeError: script_csv.main()
                
                if not self.stop_event.is_set():
                    # Refresh data on CSV completion
                    self.after(500, lambda: [self.frame_data.refresh_data(), self.frame_analytics.update_charts()])
            
            if self.stop_event.is_set():
                self.write("\n🛑 STOPPED BY USER.")
            else:
                self.write("\n✅ COMPLETED.")

        except Exception as e:
            # --- NEW ERROR HANDLING ---
            import traceback
            error_details = traceback.format_exc()
            self.write(f"\n❌ CRITICAL ERROR:\n{error_details}") 
            # --------------------------
        finally:
            self.after(0, lambda: self.sidebar.set_working_state(False))
            self.after(0, lambda: self.frame_console.show_progress(False))
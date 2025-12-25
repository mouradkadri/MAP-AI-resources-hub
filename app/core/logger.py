import sys
import queue
import datetime

class ConsoleLogger:
    def __init__(self):
        self.log_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def write(self, text):
        # Simply put the text in the queue. 
        # The UI will handle displaying it.
        if text:
            self.log_queue.put(str(text))

    def flush(self):
        pass

    def start_redirect(self):
        sys.stdout = self
        sys.stderr = self

    def stop_redirect(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def format_log(self, text):
        """
        Determines the color tag and adds a timestamp for the UI.
        """
        if not text or not text.strip(): 
            return None, None
        
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        tag = "normal"
        
        # Simple keyword matching for colors
        if any(x in text for x in ["Error", "❌", "Failed", "Exception"]):
            tag = "error"
        elif any(x in text for x in ["Success", "✅", "Added", "Saved"]):
            tag = "success"
        elif any(x in text for x in ["Warning", "⚠", "Skipped"]):
            tag = "warning"
        elif any(x in text for x in ["Scanning", "Processing", "..."]):
            tag = "info"
            
        return timestamp, tag
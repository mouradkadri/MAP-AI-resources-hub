import sys

# Try to import psutil, but don't crash if it's missing
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class SystemMonitor:
    @staticmethod
    def get_stats():
        """
        Returns a tuple (cpu_percent, ram_percent)
        or (None, None) if psutil is missing.
        """
        if not HAS_PSUTIL:
            return None, None
        
        try:
            # interval=None is non-blocking
            cpu = psutil.cpu_percent(interval=None) 
            ram = psutil.virtual_memory().percent
            return cpu, ram
        except Exception:
            return 0, 0

    @staticmethod
    def is_available():
        return HAS_PSUTIL
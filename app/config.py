import os
import configparser

class AppConfig:
    APP_TITLE = "AI Resource Intelligence Hub"
    VERSION = "v6.0 Modular Edition"
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Paths
    DATA_DIR = os.path.join(BASE_DIR, "data")
    CSV_FILE = os.path.join(DATA_DIR, "ai_resources_tagged.csv")
    CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")
    ICON_FILE = os.path.join(BASE_DIR, "assets", "icon.ico")
    RESOURCES_DIR = os.path.join(BASE_DIR, "Resources")

    # Theme
    THEME_MODE = "Dark"
    THEME_COLOR = "blue"

    @staticmethod
    def load_settings():
        config = configparser.ConfigParser()
        config.read(AppConfig.CONFIG_FILE)
        return config

    @staticmethod
    def save_settings(config_obj):
        with open(AppConfig.CONFIG_FILE, 'w') as f:
            config_obj.write(f)
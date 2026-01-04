import json
import os

DEFAULT_SETTINGS = {
    "presets": [
        {"name": "5分钟", "duration": 300, "alert_time": 60, "flash_time": 10, "music": "app/source/time.mp3"},
        {"name": "10分钟", "duration": 600, "alert_time": 60, "flash_time": 10, "music": "app/source/time.mp3"},
        {"name": "15分钟", "duration": 900, "alert_time": 60, "flash_time": 10, "music": "app/source/time.mp3"}
    ],
    "shortcuts": {
        "start_pause": "1",
        "reset": "2",
        "next_preset": "3",
        "prev_preset": "4",
        "toggle_window": "5",
        "toggle_top": "6",
        "opacity_up": "7",
        "opacity_down": "8",
        "mute": "ctrl+m"
    },
    "window": {
        "width": 350,
        "height": 250,
        "opacity": 1.0,
        "topmost": False,
        "x": 100,
        "y": 100
    },
    "theme": "light",
    "audio": {
        "volume": 0.8,
        "fade_duration": 2000,
        "prompt_regular": "app/source/非保密会议版.wav",
        "prompt_confidential": "app/source/保密会议版.wav"
    },
    "reminder": {
        "flash_seconds": 5,
        "flash_color": "#FF0000"
    },
    "display": {
        "format": "min_sec", # min_sec, seconds, percent
        "font_size": 150
    }
}

class Settings:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.data = self.load()

    def load(self):
        if not os.path.exists(self.config_file):
            return DEFAULT_SETTINGS.copy()
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Merge with default to ensure new keys exist
                return self.merge_defaults(data, DEFAULT_SETTINGS)
        except Exception:
            return DEFAULT_SETTINGS.copy()

    def merge_defaults(self, data, defaults):
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
            elif isinstance(value, dict) and isinstance(data[key], dict):
                self.merge_defaults(data[key], value)
        return data

    def save(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        keys = key.split('.')
        val = self.data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key, value):
        keys = key.split('.')
        d = self.data
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        self.save()

settings = Settings()

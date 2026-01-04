import keyboard
from PyQt5.QtCore import QObject, pyqtSignal

class ShortcutManager(QObject):
    triggered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.hotkeys = {}

    def register(self, action_name, key_sequence):
        # Remove existing if any
        if action_name in self.hotkeys:
            try:
                keyboard.remove_hotkey(self.hotkeys[action_name])
            except Exception as e:
                print(f"Failed to remove hotkey for {action_name}: {e}")
        
        if not key_sequence:
            return

        try:
            # Lambda to emit signal
            callback = lambda: self.triggered.emit(action_name)
            # Store the remover function or handle
            self.hotkeys[action_name] = keyboard.add_hotkey(key_sequence, callback)
        except Exception as e:
            print(f"Failed to register hotkey {key_sequence} for {action_name}: {e}")

    def clear(self):
        try:
            keyboard.unhook_all()
            self.hotkeys = {}
        except:
            pass

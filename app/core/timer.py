from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import time

class CountdownTimer(QObject):
    time_updated = pyqtSignal(int)  # Remaining milliseconds
    finished = pyqtSignal()
    alert_triggered = pyqtSignal() # Custom alert time reached
    flash_triggered = pyqtSignal(bool) # Flash state (True/False)

    def __init__(self):
        super().__init__()
        self.duration = 0 # milliseconds
        self.remaining = 0 # milliseconds
        self.is_running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_tick)
        self.last_time = 0
        
        self.alert_time = 0 # milliseconds
        self.alert_triggered_flag = False
        
        # Flash logic
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self._on_flash)
        self.flash_state = False
        self.flash_start_time = 5000 # Start flashing at last 5 seconds

    def set_config(self, duration_seconds, alert_seconds=0, flash_seconds=5):
        self.duration = duration_seconds * 1000
        self.alert_time = alert_seconds * 1000
        self.flash_start_time = flash_seconds * 1000
        self.reset()

    def start(self):
        if self.remaining <= 0:
            return
        self.is_running = True
        self.last_time = time.time()
        self.timer.start(20) # 50Hz update rate

    def pause(self):
        self.is_running = False
        self.timer.stop()
        self.flash_timer.stop()
        self.flash_triggered.emit(False) # Reset flash

    def toggle(self):
        if self.is_running:
            self.pause()
        else:
            self.start()

    def reset(self):
        self.pause()
        self.remaining = self.duration
        self.alert_triggered_flag = False
        self.time_updated.emit(int(self.remaining))

    def _on_tick(self):
        if not self.is_running:
            return

        current_time = time.time()
        elapsed = (current_time - self.last_time) * 1000
        self.last_time = current_time
        
        self.remaining -= elapsed
        
        # Check alerts
        if self.alert_time > 0 and self.remaining <= self.alert_time and not self.alert_triggered_flag:
            self.alert_triggered_flag = True
            self.alert_triggered.emit()

        # Check flash
        if self.remaining <= self.flash_start_time and not self.flash_timer.isActive():
            self.flash_timer.start(500) # Flash every 500ms

        if self.remaining <= 0:
            self.remaining = 0
            self.pause()
            self.finished.emit()
        
        self.time_updated.emit(int(self.remaining))

    def _on_flash(self):
        self.flash_state = not self.flash_state
        self.flash_triggered.emit(self.flash_state)

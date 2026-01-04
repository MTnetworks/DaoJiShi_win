import os
from PyQt5.QtCore import QObject, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from app.utils import get_resource_path

class AudioPlayer(QObject):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.target_volume = 80
        self.fade_timer = QTimer()
        self.fade_timer.setInterval(50) # Update every 50ms
        self.fade_timer.timeout.connect(self._update_fade)
        self.fade_step = 0
        self.fade_target = 0
        self.stop_after_fade = False

    def play(self, file_path, fade_in_duration=0):
        if not file_path:
            return
            
        # Resolve path (handle bundled files)
        resolved_path = get_resource_path(file_path)
        
        if not os.path.exists(resolved_path):
            return

        url = QUrl.fromLocalFile(resolved_path)
        content = QMediaContent(url)
        self.player.setMedia(content)
        
        if fade_in_duration > 0:
            self.player.setVolume(0)
            self.player.play()
            self.fade_to(self.target_volume, fade_in_duration)
        else:
            self.player.setVolume(self.target_volume)
            self.player.play()

    def stop(self, fade_out_duration=0):
        if fade_out_duration > 0 and self.player.state() == QMediaPlayer.PlayingState:
            self.fade_to(0, fade_out_duration, stop_after=True)
        else:
            self.player.stop()

    def set_volume(self, volume):
        self.target_volume = volume
        if not self.fade_timer.isActive():
            self.player.setVolume(volume)

    def fade_to(self, target_vol, duration, stop_after=False):
        current_vol = self.player.volume()
        diff = target_vol - current_vol
        if diff == 0:
            if stop_after:
                self.player.stop()
            return

        steps = duration / 50
        if steps <= 0:
            self.player.setVolume(target_vol)
            if stop_after:
                self.player.stop()
            return
            
        self.fade_step = diff / steps
        self.fade_target = target_vol
        self.stop_after_fade = stop_after
        self.fade_timer.start()

    def _update_fade(self):
        current_vol = self.player.volume()
        new_vol = current_vol + self.fade_step
        
        # Check bounds
        if (self.fade_step > 0 and new_vol >= self.fade_target) or \
           (self.fade_step < 0 and new_vol <= self.fade_target):
            self.player.setVolume(int(self.fade_target))
            self.fade_timer.stop()
            if self.stop_after_fade:
                self.player.stop()
        else:
            self.player.setVolume(int(new_vol))

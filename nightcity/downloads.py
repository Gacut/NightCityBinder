"""Persistent per-provider download throttling; local refreshes are unrestricted."""
import math
import time


class DownloadCooldown:
    def __init__(self, store, clock=time.time):
        self.store, self.clock = store, clock

    def remaining(self, provider):
        try:
            until = float(self.store.settings().get("download_until_" + provider, "0"))
            return min(3600, max(0, math.ceil(until - self.clock())))
        except (ValueError, OverflowError):
            return 0

    def start(self, provider):
        if self.remaining(provider):
            return False
        self.store.setting("download_until_" + provider, str(self.clock() + 3600))
        return True

    def countdown(self, provider):
        seconds = self.remaining(provider)
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

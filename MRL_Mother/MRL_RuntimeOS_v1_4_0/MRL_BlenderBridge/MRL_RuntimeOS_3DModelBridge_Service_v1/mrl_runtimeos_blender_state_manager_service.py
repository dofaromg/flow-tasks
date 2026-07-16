import bpy
import time
from typing import Callable, List

class TripoBridge3DStatus:
    def __init__(self):
        self.is_connected = False
        self.client_name = "None"
        self.last_log = ""
        self._callbacks: List[Callable[[], None]] = []
        self._last_notify_time = 0
        self._notify_interval = 0.1
        self._pending_notify = False

    def register_callback(self, fn: Callable[[], None]):
        """Register a UI callback that will be called on the main thread to refresh the UI"""
        if fn not in self._callbacks:
            self._callbacks.append(fn)

    def unregister_callback(self, fn: Callable[[], None]):
        if fn in self._callbacks:
            self._callbacks.remove(fn)

    def _notify(self):
        """Call callbacks on the main thread and trigger Blender UI redraw (via bpy.app.timers)"""
        # Debounce: avoid too frequent UI updates causing main thread blocking
        current_time = time.time()
        if current_time - self._last_notify_time < self._notify_interval:
            # If the time since the last notification is too short, mark as pending but do not notify immediately
            if not self._pending_notify:
                self._pending_notify = True
                # Delay notification until the interval has passed
                def _delayed_notify():
                    self._pending_notify = False
                    self._do_notify_now()
                    return None
                try:
                    bpy.app.timers.register(_delayed_notify, first_interval=self._notify_interval)
                except Exception:
                    pass
            return
        
        self._do_notify_now()
    
    def _do_notify_now(self):
        """Immediately perform notification"""
        self._last_notify_time = time.time()
        
        def _do_notify():
            try:
                # Call registered callbacks
                for cb in list(self._callbacks):
                    try:
                        cb()
                    except Exception:
                        pass
                # Force redraw of all window areas
                for window in bpy.context.window_manager.windows:
                    screen = window.screen
                    if not screen:
                        continue
                    for area in screen.areas:
                        try:
                            area.tag_redraw()
                        except Exception:
                            pass
            except Exception:
                pass
            return None

        # Ensure execution on the main thread
        try:
            bpy.app.timers.register(_do_notify, first_interval=0)
        except Exception:
            # Registration may fail in certain contexts; ignore to maintain stability
            pass

    def set_connected(self, client_name):
        self.is_connected = True
        self.client_name = client_name
        self._notify()

    def set_disconnected(self):
        self.is_connected = False
        self.client_name = "None"
        self._notify()

    def set_log(self, msg: str):
        self.last_log = msg
        self._notify()

status = TripoBridge3DStatus()

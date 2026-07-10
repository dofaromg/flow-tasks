import queue
import threading
import time
import bpy

from threading import Thread, Lock
from .ws_server import Server
from ..utils.logger import logger

task_manager = None

class TaskManager:
    
    def __init__(self):
        self.tasks = queue.Queue()
        self.ws_server = None
        self.ws_thread = None  # 保存WebSocket线程对象
        self._timer_running = False

    def start(self):
        # 启动定时器
        if not self._timer_running:
            self._timer_running = True
            bpy.app.timers.register(self._update, persistent=True)
            logger.info("TaskManager timer started")

        # 启动 WebSocket 服务
        if self.ws_server is None:
            self.ws_server = Server(port=60600)
            self.ws_thread = threading.Thread(target=self.ws_server.run, daemon=True)
            self.ws_thread.start()
            logger.info("WebSocket server started on port 60600")

    def _update(self):
        """
        定时器回调，每1秒处理一次任务
        """
        try:
            while not self.tasks.empty():
                task = self.tasks.get_nowait()
                self._process_task(task)
        except Exception as e:
            logger.error(f"TaskManager update error: {e}")

        return 1

    def add_task(self, task_data):
        self.tasks.put(task_data)
        logger.info(f"Task added: {task_data}")

    def _process_task(self, task):
        logger.info(f"Processing task: {task}")
        # 这里可以调用 Blender 模型加载等逻辑
        time.sleep(0.1)
        logger.info(f"Task finished: {task}")

    def stop(self):
        if self.ws_server:
            try:
                self.ws_server._direct_close()
                logger.info("WebSocket server stop requested")
            except Exception as e:
                logger.error(f"Error stopping WebSocket server: {e}")
            self.ws_server = None

        # 不等待线程，因为它是daemon线程，会在主程序退出时自动结束
        if self.ws_thread:
            logger.info("WebSocket thread will exit automatically (daemon)")
            self.ws_thread = None

        self._timer_running = False

def register():
    global task_manager
    if task_manager is None:
        task_manager = TaskManager()
        task_manager.start()
        logger.info("TaskManager registered")


def unregister():
    global task_manager
    if task_manager:
        task_manager.stop()
        task_manager = None
        logger.info("TaskManager unregistered")
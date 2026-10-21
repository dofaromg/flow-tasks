from typing import Optional

import asyncio
import json
import uuid
import traceback
import bpy
import time
from functools import partial

from ..lib.websockets.server import serve
from ..lib.websockets.exceptions import ConnectionClosed
from ..utils.logger import logger
from .status_manager import status
from .file_transfer import FileTransferManager


class Server:
    """
    Blender WebSocket 服务端
    
    职责：
    - 管理 WebSocket 连接
    - 处理客户端消息（握手、心跳、文件传输）
    - 维护客户端状态
    """
    _host = "127.0.0.1"
    _port = 60600
    _server = None
    
    def __init__(self, port=None):
        self.host = self._host
        self.port = port or self._port
        self._sockets = {}
        self._handlers = {}
        self._binary_handlers = {}
        self.stop_event = asyncio.Event()
        self._succeeded_task = {}
        self._pending_tasks = {}   

        self._transfer_manager = None
        self._client_info = {}
        self._last_ping_time = {}
        self._heartbeat_timeout = 30
        self._heartbeat_task = None

        # Register message handlers
        self.reg_handler("_default", self._default) 
        self.reg_handler("ping", self._ping)
        self.reg_handler("handshake", self._handshake)
        self.reg_binary_handler("file_transfer", self._handle_file_transfer_blob)

    def reg_handler(self, event_type, handler):
        self._handlers[event_type] = handler
    
    def reg_binary_handler(self, event_type, handler):
        self._binary_handlers[event_type] = handler

    def run(self):
        """Run the WebSocket server (called in a separate thread)"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._main())
        except Exception as e:
            logger.error(f"Error in event loop: {e}")
            # Check if the error is due to port being in use, update UI in main thread using timer
            error_msg = str(e)
            if "10048" in error_msg or "address already in use" in error_msg.lower():
                self._schedule_ui_update(f"Port {self.port} is already in use")
            else:
                self._schedule_ui_update(f"Server error: {error_msg[:50]}")
        finally:
            # Ensure the event loop is closed
            try:
                self.loop.close()
                logger.info("Event loop closed")
            except Exception as e:
                logger.error(f"Error closing event loop: {e}")

    def _direct_close(self):
        if not hasattr(self, "loop"):
            return
            
        try:
            if self.loop and not self.loop.is_closed():
                self.loop.call_soon_threadsafe(self.stop_event.set)
                logger.info("Stopping WebSocket server...")
        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")

    def _schedule_ui_update(self, message):
        """Schedule UI update on the main thread"""
        bpy.app.timers.register(partial(self._update_status_log, message), first_interval=0)
    
    def _update_status_log(self, message):
        """Update status log on the main thread"""
        status.set_log(message)
        return None

    def pop_task_all(self, sid):
        if sid and sid in self._pending_tasks:
            tasks = self._pending_tasks.pop(sid, [])
            logger.info(f"Cleared {len(tasks)} tasks for session {sid}")
        else:
            logger.debug(f"No pending tasks found for session {sid}")

    # ==================== Core ====================
    
    async def _main(self):
        async with serve(self.handle, self.host, self.port, max_size=None) as server:
            Server._server = server
            logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
            status.set_log(f"Server running on port:{self.port}")
            
            # 启动心跳检测任务
            self._heartbeat_task = asyncio.create_task(self._check_heartbeat())
            logger.info(f"Heartbeat monitoring started (timeout: {self._heartbeat_timeout}s)")
            
            await self.stop_event.wait()
            
            # 取消心跳检测任务
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # 取消所有pending任务
            pending = [task for task in asyncio.all_tasks(self.loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                try:
                    await asyncio.wait(pending, timeout=2.0)
                    logger.info(f"Cancelled {len(pending)} pending tasks")
                except asyncio.CancelledError:
                    logger.debug("Tasks cancelled during shutdown")
                    pass

    async def handle(self, websocket, path):
        """Handle a single WebSocket connection"""
        sid = str(uuid.uuid4())
        client_id = id(websocket)
        
        # Close all existing connections, keep only the newest
        if self._sockets:
            logger.info(f"Closing {len(self._sockets)} existing client(s) to accept new connection")
            status.set_log(f"Closing {len(self._sockets)} existing connection(s)")
            old_sockets = list(self._sockets.items())
            self._sockets.clear()
            for old_sid, old_ws in old_sockets:
                try:
                    old_client_id = id(old_ws)
                    self._last_ping_time.pop(old_client_id, None)
                    await old_ws.close(1000, "New client connected")
                except Exception as e:
                    logger.warning(f"Error closing old websocket: {e}")
        
        self._sockets[sid] = websocket
        self._last_ping_time[client_id] = time.time()
        logger.info(f"Client connected: {sid} (client_id: {client_id})")

        try:
            client_ip = websocket.remote_address[0] if websocket.remote_address else "Unknown"
            status.set_connected(f"{client_ip} ({sid[:8]})")
            status.set_log("Client connected successfully.")
        except Exception as e:
            logger.warning(f"Failed to set status: {e}")

        try:
            async for message in websocket:
                try:
                    # Unified processing: convert message to bytes, parse JSON header
                    data_bytes = message if isinstance(message, (bytes, bytearray)) else message.encode('utf-8')
                    
                    # Parse JSON part
                    json_end = self._find_json_end(data_bytes)
                    if json_end == -1:
                        logger.error("No valid JSON found in message")
                        continue
                    
                    # Parse JSON metadata
                    json_bytes = data_bytes[0:json_end]
                    parsed_data = json.loads(json_bytes.decode('utf-8'))
                    msg_type = parsed_data.get('type', '_default')
                    
                    # Dispatch based on type
                    if msg_type in self._binary_handlers:
                        await self._binary_handlers[msg_type](websocket, data_bytes)
                    else:
                        if msg_type != "ping":
                            status.set_log(f"Received {msg_type} event")
                        await self._handlers.get(msg_type, self._default)(websocket, parsed_data)
                except ConnectionClosed:
                    logger.debug(f"Connection closed while handling message for client {sid}")
                    raise
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    traceback.print_exc()
                    if isinstance(e, (asyncio.CancelledError, KeyboardInterrupt)):
                        raise
        except ConnectionClosed as e:
            logger.info(f"Client disconnected: {sid} (code: {e.code}, reason: {e.reason})")
            status.set_disconnected()
            status.set_log(f"Client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error for client {sid}: {e}")
            traceback.print_exc()
            status.set_disconnected()
            status.set_log(f"Connection error: {str(e)[:50]}")
        finally:
            # Clean up connections and update status
            self._sockets.pop(sid, None)
            client_id = id(websocket)
            self._client_info.pop(client_id, None)
            self._last_ping_time.pop(client_id, None)
            
            if not self._sockets:
                status.set_disconnected()
                status.set_log("All connections closed")
                logger.info("No active connections remaining")

    # ==================== Message Handlers ====================
    
    async def _handshake(self, websocket, event):
        payload = event.get("payload", {})
        client_name = payload.get("clientName", "Unknown")
        protocol_version = payload.get("protocolVersion", "1.0.0")
        
        logger.info(f"Handshake from {client_name}, protocol version: {protocol_version}")
        
        # Save client information
        client_id = id(websocket)
        self._client_info[client_id] = {
            "clientName": client_name,
            "protocolVersion": protocol_version
        }
        
        # Respond to handshake confirmation
        response = {
            "type": "handshake_ack",
            "payload": {
                "success": True,
                "clientName": "Blender",
                "dccVersion": bpy.app.version_string,
                "pluginVersion": "1.0.0",
                "protocolVersion": "1.0.0"
            }
        }
        if await self._safe_send(websocket, response, "handshake_ack"):
            status.set_log(f"Connected with {client_name}")

    async def _ping(self, websocket, event):
        client_id = id(websocket)
        current_time = time.time()
        self._last_ping_time[client_id] = current_time
        # logger.debug(f"Received ping from client {client_id} at {time.strftime('%H:%M:%S', time.localtime(current_time))}")
        await self._safe_send(websocket, {"type": "pong"}, "pong response")

    async def _default(self, websocket, message):
        logger.warning(f"Default handler: {message}")
        await self._safe_send(websocket, {"type": "default", "data": message}, "default response")

    async def _check_heartbeat(self):
        while not self.stop_event.is_set():
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                current_time = time.time()
                disconnected_clients = []
                
                for sid, websocket in list(self._sockets.items()):
                    client_id = id(websocket)
                    last_ping = self._last_ping_time.get(client_id)
                    
                    if last_ping is None:
                        logger.warning(f"Client {sid} has no ping record")
                        continue
                    
                    # Check for timeout
                    elapsed = current_time - last_ping
                    if elapsed > self._heartbeat_timeout:
                        logger.warning(f"Client {sid} heartbeat timeout ({elapsed:.1f}s > {self._heartbeat_timeout}s)")
                        disconnected_clients.append((sid, websocket))
                
                # Disconnect timed-out clients
                for sid, websocket in disconnected_clients:
                    try:
                        await websocket.close(1001, "Heartbeat timeout")
                        logger.info(f"Closed connection for client {sid} due to heartbeat timeout")
                        status.set_log(f"Client timeout, closing connection")
                    except Exception as e:
                        logger.error(f"Error closing timed-out websocket {sid}: {e}")
                    finally:
                        self._sockets.pop(sid, None)
                        client_id = id(websocket)
                        self._last_ping_time.pop(client_id, None)
                        self._client_info.pop(client_id, None)
                
                # If there are timed-out clients and no remaining connections, update status
                if disconnected_clients and not self._sockets:
                    status.set_disconnected()
                    status.set_log("Client disconnected (heartbeat timeout)")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat check: {e}")
                traceback.print_exc()

    # ==================== Helper Methods ====================
    
    async def _safe_send(self, websocket, message_dict, error_context="", timeout=5.0):
        """Safely send a message, handling connection closures and other exceptions"""
        try:
            if hasattr(websocket, 'close_code') and websocket.close_code is not None:
                logger.debug(f"Websocket already closed (code: {websocket.close_code}), skipping send")
                return False
            
            await asyncio.wait_for(
                websocket.send(json.dumps(message_dict)),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout sending {error_context} (>{timeout}s)")
            return False
        except ConnectionClosed as e:
            logger.debug(f"Connection closed while sending {error_context}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to send {error_context}: {e}")
            return False

    def _find_json_end(self, data_bytes: bytes) -> int:
        """Find the end position of JSON"""
        json_end = -1
        brace_count = 0
        in_string = False
        escape = False
        
        for i, byte in enumerate(data_bytes):
            char = chr(byte) if byte < 128 else None
            if char is None:
                continue
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
        
        return json_end

    async def _handle_file_transfer_blob(self, websocket, data: bytes):
        try:
            json_end = self._find_json_end(data)
            
            if json_end == -1:
                await self._send_file_transfer_error(websocket, None, 0, 1001, "Invalid blob format: JSON not found")
                return
            
            json_bytes = data[0:json_end]
            metadata = json.loads(json_bytes.decode('utf-8'))
            
            # 从payload中获取实际数据
            payload = metadata.get('payload', {})
            file_type = payload.get('fileType')
            file_id = payload.get('fileId')
            file_name = payload.get('fileName')
            chunk_total = payload.get('chunkTotal')
            chunk_index = payload.get('chunkIndex')
            chunk_size = payload.get('chunkSize')
            
            # 获取二进制数据部分
            blob_data = data[json_end:]
            
            logger.info(f"Received file chunk: {file_id}, index {chunk_index}/{chunk_total}, type: {file_type}, size: {len(blob_data)} (expected: {chunk_size})")
            
            # 初始化传输管理器
            if self._transfer_manager is None:
                self._transfer_manager = FileTransferManager()
            
            # 添加分片
            session = self._transfer_manager.get_or_create_session(
                file_id, chunk_total, file_type, file_name
            )
            session.add_chunk(chunk_index, blob_data)
            
            # 发送确认
            await self._send_file_transfer_ack(websocket, file_id, chunk_index, True)
            
            # 检查是否完成
            if session.is_complete():
                logger.info(f"File transfer complete for {file_id}, assembling...")
                assembled_data = session.assemble()
                
                model_name = session.file_name
                logger.info(f"Received complete model name: {model_name}")
                status.set_log(f"receive model: {model_name}")
                
                from .model_loader import loader
                
                try:
                    # 保存临时文件
                    temp_filename = f"{file_id}.{file_type}"
                    file_path = loader.cache_manager.save_file(temp_filename, assembled_data)
                    
                    # 发送文件传输完成消息
                    await self._safe_send(websocket, {
                        "type": "file_transfer_complete",
                        "payload": {
                            "fileId": file_id,
                            "status": "importing",
                            "message": "File transfer complete, importing model..."
                        }
                    }, "file_transfer_complete")
                    
                    # 保存websocket引用用于导入完成后通知
                    ws_ref = websocket
                    
                    # 使用定时器在主线程执行导入
                    def import_job():
                        try:
                            loader._import_model_file(file_path, file_type)
                            loader.cache_manager.cleanup_file(file_path)
                            logger.info(f"Successfully imported {file_id}")
                            
                            # 通知前端导入成功
                            if hasattr(self, 'loop') and not self.loop.is_closed():
                                asyncio.run_coroutine_threadsafe(
                                    self._safe_send(ws_ref, {
                                        "type": "import_complete",
                                        "payload": {
                                            "fileId": file_id,
                                            "success": True,
                                            "message": "Model imported successfully"
                                        }
                                    }, "import_complete"),
                                    self.loop
                                )
                            else:
                                logger.warning("Event loop closed, cannot send import_complete")
                        except Exception as e:
                            logger.error(f"Failed to import {file_id}: {e}")
                            
                            # 通知前端导入失败
                            if hasattr(self, 'loop') and not self.loop.is_closed():
                                asyncio.run_coroutine_threadsafe(
                                    self._safe_send(ws_ref, {
                                        "type": "import_complete",
                                        "payload": {
                                            "fileId": file_id,
                                            "success": False,
                                            "message": str(e)
                                        }
                                    }, "import_complete"),
                                    self.loop
                                )
                            else:
                                logger.warning("Event loop closed, cannot send import_complete error")
                        return None
                    
                    bpy.app.timers.register(import_job, first_interval=0)
                    
                    # 清理会话
                    self._transfer_manager.remove_session(file_id)
                    
                except Exception as e:
                    logger.error(f"Failed to process complete file {file_id}: {e}")
                    await self._send_file_transfer_error(websocket, file_id, chunk_index, 1002, str(e))
                    self._transfer_manager.remove_session(file_id)
                    
        except Exception as e:
            logger.error(f"Error in _handle_file_transfer_blob: {e}")
            traceback.print_exc()

    async def _send_file_transfer_ack(self, websocket, file_id: Optional[str], file_index: int, success: bool, code: Optional[int] = None):
        response = {
            "type": "file_transfer_ack",
            "payload": {
                "success": success,
                "fileId": file_id,
                "fileIndex": file_index
            }
        }
        if code is not None:
            response["payload"]["code"] = code
        
        await self._safe_send(websocket, response, "file_transfer_ack")

    async def _send_file_transfer_error(self, websocket, file_id: Optional[str], file_index: int, code: int, message: str = ""):
        response = {
            "type": "file_transfer_ack",
            "payload": {
                "success": False,
                "fileId": file_id,
                "fileIndex": file_index,
                "code": code
            }
        }
        await self._safe_send(websocket, response, "file_transfer_error")
        if message:
            logger.error(f"File transfer error: {code} - {message}")



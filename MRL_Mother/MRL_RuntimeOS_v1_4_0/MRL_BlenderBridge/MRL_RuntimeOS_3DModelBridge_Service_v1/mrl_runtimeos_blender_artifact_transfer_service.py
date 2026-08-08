import threading
import time


class FileTransferManager:
    def __init__(self):
        self._sessions = {}  # file_id -> FileTransferSession
        self._lock = threading.Lock()
    
    def get_or_create_session(self, file_id: str, total_chunks: int, file_type: str, file_name: str = None):
        with self._lock:
            if file_id not in self._sessions:
                self._sessions[file_id] = FileTransferSession(file_id, total_chunks, file_type, file_name)
            return self._sessions[file_id]
    
    def get_session(self, file_id: str):
        with self._lock:
            return self._sessions.get(file_id)
    
    def remove_session(self, file_id: str):
        with self._lock:
            self._sessions.pop(file_id, None)


class FileTransferSession:
    def __init__(self, file_id: str, total_chunks: int, file_type: str, file_name: str = None):
        self.file_id = file_id
        self.total_chunks = total_chunks
        self.file_type = file_type
        self.file_name = file_name or file_id
        self.chunks = {}  # index -> data
        self._lock = threading.Lock()
        self.created_at = time.time()
    
    def add_chunk(self, index: int, data: bytes):
        with self._lock:
            self.chunks[index] = data
    
    def is_complete(self) -> bool:
        with self._lock:
            return len(self.chunks) == self.total_chunks
    
    def assemble(self) -> bytes:
        with self._lock:
            result = b''
            for i in range(self.total_chunks):
                if i not in self.chunks:
                    raise ValueError(f"Missing chunk {i}")
                result += self.chunks[i]
            return result

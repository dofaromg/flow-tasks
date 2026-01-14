#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Particle Wire Bridge
粒子線協橋接層

Provides bidirectional conversion between Python particle data
and PD_AI C wire protocol format.

Features:
- Python dict → Wire format (bytes)
- Wire format → Python dict
- Integration with AdvancedParticleCompressor
- Support for all wire protocol message types
"""

import struct
import json
from typing import Dict, Any, Optional, Tuple
from ctypes import Structure, c_uint8, c_uint32, sizeof
from datetime import datetime

# Import compressor from memory module
try:
    from memory_quick_mount import AdvancedParticleCompressor
except ImportError:
    # Fallback if running standalone
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from memory_quick_mount import AdvancedParticleCompressor


# ============================================================================
# Wire Protocol Constants (matching PD_AI_wire.h)
# ============================================================================

# Message types
M_PING = 0x00
M_PONG = 0x01
M_UPSERT = 0x02
M_QUERY = 0x03
M_DELETE = 0x04
M_SNAPSHOT = 0x05
M_RESTORE = 0x06
M_SYNC = 0x07

# Key classes
K_MCP = 0x10
K_AUTH = 0x20
K_CONFIG = 0x30
K_STATE = 0x40
K_SNAPSHOT = 0x50
K_METADATA = 0x60

# Annotation bits
T_R = 0x01  # Read
T_W = 0x02  # Write
T_D = 0x04  # Delete
T_X = 0x08  # Execute
T_SYNC = 0x10
T_COMPRESS = 0x20
T_ENCRYPT = 0x40
T_ARCHIVE = 0x80

# Combined annotations
ANN_MCP = T_R | T_W | T_D
ANN_RO = T_R
ANN_RW = T_R | T_W
ANN_FULL = T_R | T_W | T_D | T_X

# Capability flags
P_TOOLS = 0x10000000
P_APPS = 0x20000000
P_FILES = 0x40000000
P_NETWORK = 0x80000000
P_DATABASE = 0x01000000
P_COMPUTE = 0x02000000
P_MEMORY = 0x04000000
P_ADMIN = 0x08000000

# Combined capabilities
CAP_STANDARD = P_TOOLS | P_APPS
CAP_EXTENDED = P_TOOLS | P_APPS | P_FILES


# ============================================================================
# Wire Protocol Structures
# ============================================================================

class WireHeader(Structure):
    """
    Wire Header - 16 bytes packed structure
    Matches wh16_t from PD_AI_wire.h
    """
    _pack_ = 1  # Pack structure (no padding)
    _fields_ = [
        ("mt", c_uint8),    # message type
        ("kc", c_uint8),    # key class
        ("ann", c_uint8),   # annotation bits
        ("ver", c_uint8),   # version
        ("cap", c_uint32),  # capabilities
        ("rid", c_uint32),  # record ID
        ("n", c_uint32)     # payload size
    ]
    
    def __repr__(self):
        return (f"WireHeader(mt=0x{self.mt:02x}, kc=0x{self.kc:02x}, "
                f"ann=0x{self.ann:02x}, ver={self.ver}, "
                f"cap=0x{self.cap:08x}, rid={self.rid}, n={self.n})")


class KeyValuePair(Structure):
    """
    Key-Value Pair - 8 bytes packed structure
    Matches kv32_t from PD_AI_wire.h
    """
    _pack_ = 1
    _fields_ = [
        ("k", c_uint32),  # key
        ("v", c_uint32)   # value
    ]
    
    def __repr__(self):
        return f"KV(k=0x{self.k:08x}, v=0x{self.v:08x})"


class Budget(Structure):
    """
    Budget Structure - 12 bytes packed structure
    Matches bud_t from PD_AI_wire.h
    """
    _pack_ = 1
    _fields_ = [
        ("mode", c_uint32),         # budget mode
        ("cap_credits", c_uint32),  # capacity
        ("used_credits", c_uint32)  # used
    ]
    
    def __repr__(self):
        return (f"Budget(mode={self.mode}, cap={self.cap_credits}, "
                f"used={self.used_credits})")


# ============================================================================
# Particle Wire Bridge
# ============================================================================

class ParticleWireBridge:
    """
    粒子線協橋接器 (Particle Wire Bridge)
    
    Provides bidirectional conversion between Python particle data
    and PD_AI C wire protocol format.
    """
    
    def __init__(self, use_compression: bool = True):
        """
        Initialize bridge
        
        Args:
            use_compression: Enable particle compression
        """
        self.compressor = AdvancedParticleCompressor() if use_compression else None
        self.use_compression = use_compression
        self.conversion_log = []
    
    def python_to_wire(
        self,
        data: Dict[str, Any],
        msg_type: int = M_UPSERT,
        key_class: int = K_MCP,
        annotation: int = ANN_MCP,
        capabilities: int = CAP_STANDARD,
        record_id: int = 1
    ) -> bytes:
        """
        將 Python 粒子壓縮結果轉為 PD_AI wire 格式
        Convert Python data to PD_AI wire format
        
        Args:
            data: Python dictionary to convert
            msg_type: Message type (default: M_UPSERT)
            key_class: Key class (default: K_MCP)
            annotation: Annotation bits (default: ANN_MCP)
            capabilities: Capability flags (default: CAP_STANDARD)
            record_id: Record ID (default: 1)
            
        Returns:
            Wire format bytes (header + payload)
        """
        # Compress if enabled
        if self.use_compression and self.compressor:
            compressed = self.compressor.compress(data)
            payload_data = compressed
        else:
            payload_data = data
        
        # Convert to JSON payload
        payload_json = json.dumps(payload_data, ensure_ascii=False)
        payload_bytes = payload_json.encode('utf-8')
        payload_size = len(payload_bytes)
        
        # Create wire header
        header = WireHeader(
            mt=msg_type,
            kc=key_class,
            ann=annotation,
            ver=1,  # Version 1
            cap=capabilities,
            rid=record_id,
            n=payload_size
        )
        
        # Combine header and payload
        wire_data = bytes(header) + payload_bytes
        
        # Log conversion
        self.conversion_log.append({
            "direction": "python_to_wire",
            "timestamp": datetime.now().isoformat(),
            "header_size": sizeof(WireHeader),
            "payload_size": payload_size,
            "total_size": len(wire_data),
            "msg_type": msg_type,
            "compressed": self.use_compression
        })
        
        return wire_data
    
    def wire_to_python(self, wire_data: bytes) -> Tuple[Dict[str, Any], WireHeader]:
        """
        解析 wire 格式回 Python 物件
        Parse wire format back to Python object
        
        Args:
            wire_data: Wire format bytes
            
        Returns:
            Tuple of (restored_data, header)
        """
        if len(wire_data) < sizeof(WireHeader):
            raise ValueError(f"Wire data too short: {len(wire_data)} bytes")
        
        # Extract header
        header = WireHeader.from_buffer_copy(wire_data[:sizeof(WireHeader)])
        
        # Extract payload
        payload_start = sizeof(WireHeader)
        payload_end = payload_start + header.n
        
        if len(wire_data) < payload_end:
            raise ValueError(
                f"Incomplete payload: expected {header.n} bytes, "
                f"got {len(wire_data) - payload_start} bytes"
            )
        
        payload_bytes = wire_data[payload_start:payload_end]
        payload_json = payload_bytes.decode('utf-8')
        payload_data = json.loads(payload_json)
        
        # Decompress if needed
        if self.use_compression and self.compressor:
            if isinstance(payload_data, dict) and "_particle_type" in payload_data:
                restored_data = self.compressor.decompress(payload_data)
            else:
                restored_data = payload_data
        else:
            restored_data = payload_data
        
        # Log conversion
        self.conversion_log.append({
            "direction": "wire_to_python",
            "timestamp": datetime.now().isoformat(),
            "header_size": sizeof(WireHeader),
            "payload_size": header.n,
            "total_size": len(wire_data),
            "msg_type": header.mt,
            "compressed": self.use_compression
        })
        
        return restored_data, header
    
    def create_snapshot_message(
        self,
        agent_name: str,
        state: Dict[str, Any],
        record_id: int = 0x10000001  # Snapshot ID range
    ) -> bytes:
        """
        建立快照訊息 (Create snapshot message)
        
        Args:
            agent_name: Agent name
            state: State to snapshot
            record_id: Record ID in snapshot range
            
        Returns:
            Wire format snapshot message
        """
        snapshot_data = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "state": state
        }
        
        return self.python_to_wire(
            snapshot_data,
            msg_type=M_SNAPSHOT,
            key_class=K_SNAPSHOT,
            annotation=ANN_MCP | T_COMPRESS,
            record_id=record_id
        )
    
    def create_query_message(
        self,
        query_params: Dict[str, Any],
        record_id: int = 1
    ) -> bytes:
        """
        建立查詢訊息 (Create query message)
        
        Args:
            query_params: Query parameters
            record_id: Record ID to query
            
        Returns:
            Wire format query message
        """
        return self.python_to_wire(
            query_params,
            msg_type=M_QUERY,
            key_class=K_MCP,
            annotation=ANN_RO,  # Read-only for queries
            record_id=record_id
        )
    
    def get_conversion_log(self) -> list:
        """Get conversion history"""
        return self.conversion_log.copy()
    
    def clear_log(self):
        """Clear conversion log"""
        self.conversion_log.clear()


# ============================================================================
# Helper Functions
# ============================================================================

def format_wire_hex(wire_data: bytes, bytes_per_line: int = 16) -> str:
    """
    Format wire data as hex dump
    
    Args:
        wire_data: Wire format bytes
        bytes_per_line: Number of bytes per line
        
    Returns:
        Formatted hex dump string
    """
    lines = []
    for i in range(0, len(wire_data), bytes_per_line):
        chunk = wire_data[i:i+bytes_per_line]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"{i:04x}  {hex_str:<{bytes_per_line*3}}  {ascii_str}")
    return '\n'.join(lines)


def main():
    """Demo and test for Particle Wire Bridge"""
    print("=" * 60)
    print("Particle Wire Bridge Demo")
    print("=" * 60)
    
    # Create bridge
    bridge = ParticleWireBridge(use_compression=True)
    
    # Test data
    test_data = {
        "主體": "Agent-01",
        "任務": "資料處理",
        "狀態": "執行中",
        "進度": 75
    }
    
    print("\n1. Original Data:")
    print(json.dumps(test_data, ensure_ascii=False, indent=2))
    
    # Python → Wire
    print("\n2. Converting Python → Wire...")
    wire_data = bridge.python_to_wire(test_data)
    print(f"   Wire data size: {len(wire_data)} bytes")
    print(f"   Header: {sizeof(WireHeader)} bytes")
    print(f"   Payload: {len(wire_data) - sizeof(WireHeader)} bytes")
    
    print("\n3. Wire format (hex dump):")
    print(format_wire_hex(wire_data))
    
    # Wire → Python
    print("\n4. Converting Wire → Python...")
    restored_data, header = bridge.wire_to_python(wire_data)
    print(f"   Header: {header}")
    print(f"   Restored data:")
    print(json.dumps(restored_data, ensure_ascii=False, indent=2))
    
    # Verify round-trip
    print("\n5. Round-trip verification:")
    if restored_data == test_data:
        print("   ✓ Round-trip successful!")
    else:
        print("   ✗ Round-trip failed!")
        print("   Differences detected")
    
    # Conversion log
    print("\n6. Conversion log:")
    for entry in bridge.get_conversion_log():
        print(f"   {entry['direction']}: {entry['total_size']} bytes "
              f"({entry['timestamp']})")


if __name__ == "__main__":
    main()

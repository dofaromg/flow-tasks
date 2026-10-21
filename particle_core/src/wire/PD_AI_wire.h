#ifndef PD_AI_WIRE_H
#define PD_AI_WIRE_H

#include <stdint.h>

/**
 * PD_AI Wire Protocol Header
 * MCP (Memory Control Protocol) wire format definitions
 * 
 * 16-byte header + variable payload structure for cross-language
 * state persistence and memory management
 */

// ============================================================================
// Core Structure Definitions
// ============================================================================

/**
 * Wire Header - 16 bytes packed structure
 * Layout: mt(1) + kc(1) + ann(1) + ver(1) + cap(4) + rid(4) + n(4) = 16 bytes
 */
typedef struct {
    uint8_t  mt;      // message type (M_UPSERT=0x02, M_QUERY=0x03, etc.)
    uint8_t  kc;      // key class (K_MCP=0x10, K_AUTH=0x20, etc.)
    uint8_t  ann;     // annotation bits (T_R=0x01, T_W=0x02, T_D=0x04)
    uint8_t  ver;     // version (currently 1)
    uint32_t cap;     // capabilities bitmap
    uint32_t rid;     // record ID
    uint32_t n;       // payload size in bytes
} __attribute__((packed)) wh16_t;

/**
 * Key-Value Pair - 8 bytes packed structure
 * Used for metadata and configuration data
 */
typedef struct {
    uint32_t k;       // key
    uint32_t v;       // value
} __attribute__((packed)) kv32_t;

/**
 * Budget Structure - 12 bytes packed structure
 * Tracks resource usage and limits
 */
typedef struct {
    uint32_t mode;         // budget mode
    uint32_t cap_credits;  // capacity/maximum credits
    uint32_t used_credits; // used credits
} __attribute__((packed)) bud_t;

// ============================================================================
// Message Type Constants
// ============================================================================

#define M_PING       0x00  // Ping/heartbeat message
#define M_PONG       0x01  // Pong/acknowledgment
#define M_UPSERT     0x02  // Insert or update record
#define M_QUERY      0x03  // Query/read record
#define M_DELETE     0x04  // Delete record
#define M_SNAPSHOT   0x05  // Create state snapshot
#define M_RESTORE    0x06  // Restore from snapshot
#define M_SYNC       0x07  // Synchronization request

// ============================================================================
// Key Class Constants
// ============================================================================

#define K_MCP        0x10  // Memory Control Protocol keys
#define K_AUTH       0x20  // Authentication keys
#define K_CONFIG     0x30  // Configuration keys
#define K_STATE      0x40  // State data keys
#define K_SNAPSHOT   0x50  // Snapshot keys
#define K_METADATA   0x60  // Metadata keys

// ============================================================================
// Annotation Bits (Permissions/Flags)
// ============================================================================

#define T_R          0x01  // Read permission
#define T_W          0x02  // Write permission
#define T_D          0x04  // Delete permission
#define T_X          0x08  // Execute permission
#define T_SYNC       0x10  // Sync flag
#define T_COMPRESS   0x20  // Compression enabled
#define T_ENCRYPT    0x40  // Encryption enabled
#define T_ARCHIVE    0x80  // Archived/sealed

// Combined annotation patterns
#define ANN_MCP      (T_R | T_W | T_D)           // Standard MCP permissions
#define ANN_RO       (T_R)                        // Read-only
#define ANN_RW       (T_R | T_W)                  // Read-write
#define ANN_FULL     (T_R | T_W | T_D | T_X)     // Full permissions

// ============================================================================
// Capability Flags
// ============================================================================

#define P_TOOLS      0x10000000  // Tool access capability
#define P_APPS       0x20000000  // Application access capability
#define P_FILES      0x40000000  // File system access
#define P_NETWORK    0x80000000  // Network access
#define P_DATABASE   0x01000000  // Database access
#define P_COMPUTE    0x02000000  // Compute resources
#define P_MEMORY     0x04000000  // Memory management
#define P_ADMIN      0x08000000  // Admin privileges

// Combined capability patterns
#define CAP_STANDARD (P_TOOLS | P_APPS)          // Standard capabilities
#define CAP_EXTENDED (P_TOOLS | P_APPS | P_FILES)
#define CAP_FULL     0xFFFFFFFF                   // All capabilities

// ============================================================================
// Record ID Ranges
// ============================================================================

#define RID_SYSTEM_MIN    0x00000001  // System records start
#define RID_SYSTEM_MAX    0x000FFFFF  // System records end
#define RID_USER_MIN      0x00100000  // User records start
#define RID_USER_MAX      0x0FFFFFFF  // User records end
#define RID_SNAPSHOT_MIN  0x10000000  // Snapshot records start
#define RID_SNAPSHOT_MAX  0x1FFFFFFF  // Snapshot records end
#define RID_TEMP_MIN      0x20000000  // Temporary records start
#define RID_TEMP_MAX      0x2FFFFFFF  // Temporary records end

// ============================================================================
// Convenience Macros
// ============================================================================

/**
 * Create a wire header with specified parameters
 */
#define WH(mt, kc, ann, cap, rid, n) \
    ((wh16_t){mt, kc, ann, 1, cap, rid, n})

/**
 * Create a key-value pair
 */
#define KV(k, v) \
    ((kv32_t){k, v})

/**
 * Create a budget structure
 */
#define BUD(mode, cap, used) \
    ((bud_t){mode, cap, used})

/**
 * Calculate bytes needed for N key-value pairs
 */
#define BYTES_KV(n) \
    ((n) * sizeof(kv32_t))

/**
 * Calculate total message size (header + payload)
 */
#define MSG_SIZE(payload_bytes) \
    (sizeof(wh16_t) + (payload_bytes))

// ============================================================================
// Validation Macros
// ============================================================================

/**
 * Check if record ID is in valid range
 */
#define RID_IS_VALID(rid) \
    ((rid) >= RID_SYSTEM_MIN && (rid) <= RID_TEMP_MAX)

/**
 * Check if record ID is in system range
 */
#define RID_IS_SYSTEM(rid) \
    ((rid) >= RID_SYSTEM_MIN && (rid) <= RID_SYSTEM_MAX)

/**
 * Check if record ID is in user range
 */
#define RID_IS_USER(rid) \
    ((rid) >= RID_USER_MIN && (rid) <= RID_USER_MAX)

/**
 * Check if annotation has read permission
 */
#define HAS_READ(ann) \
    (((ann) & T_R) != 0)

/**
 * Check if annotation has write permission
 */
#define HAS_WRITE(ann) \
    (((ann) & T_W) != 0)

/**
 * Check if annotation has delete permission
 */
#define HAS_DELETE(ann) \
    (((ann) & T_D) != 0)

#endif // PD_AI_WIRE_H

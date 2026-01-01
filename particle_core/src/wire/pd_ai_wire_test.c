#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "PD_AI_wire.h"

/**
 * PD_AI Wire Protocol Test Suite
 * Tests for wire format structures, macros, and message assembly
 */

// Test counters
static int tests_run = 0;
static int tests_passed = 0;

// Test helper macros
#define TEST_START(name) \
    do { \
        printf("\n[TEST] %s\n", name); \
        tests_run++; \
    } while(0)

#define TEST_PASS() \
    do { \
        tests_passed++; \
        printf("  ✓ PASSED\n"); \
    } while(0)

#define TEST_FAIL(msg) \
    do { \
        printf("  ✗ FAILED: %s\n", msg); \
        return 0; \
    } while(0)

#define ASSERT_EQ(a, b, msg) \
    do { \
        if ((a) != (b)) { \
            printf("  ✗ FAILED: %s (expected %d, got %d)\n", msg, (int)(b), (int)(a)); \
            return 0; \
        } \
    } while(0)

#define ASSERT_TRUE(cond, msg) \
    do { \
        if (!(cond)) { \
            printf("  ✗ FAILED: %s\n", msg); \
            return 0; \
        } \
    } while(0)

// ============================================================================
// Test Functions
// ============================================================================

/**
 * Test 1: Wire Header Structure (wh16_t)
 * Verify 16-byte header layout and field access
 */
int test_wh16() {
    TEST_START("test_wh16 - Wire Header Structure");
    
    // Test structure size
    ASSERT_EQ(sizeof(wh16_t), 16, "Header size must be 16 bytes");
    
    // Test macro construction
    wh16_t header = WH(M_UPSERT, K_MCP, ANN_MCP, P_TOOLS | P_APPS, 1, 100);
    
    ASSERT_EQ(header.mt, M_UPSERT, "Message type mismatch");
    ASSERT_EQ(header.kc, K_MCP, "Key class mismatch");
    ASSERT_EQ(header.ann, ANN_MCP, "Annotation mismatch");
    ASSERT_EQ(header.ver, 1, "Version mismatch");
    ASSERT_EQ(header.cap, P_TOOLS | P_APPS, "Capabilities mismatch");
    ASSERT_EQ(header.rid, 1, "Record ID mismatch");
    ASSERT_EQ(header.n, 100, "Payload size mismatch");
    
    printf("  - Header size: %zu bytes\n", sizeof(wh16_t));
    printf("  - mt=%02x kc=%02x ann=%02x ver=%d\n", 
           header.mt, header.kc, header.ann, header.ver);
    printf("  - cap=%08x rid=%08x n=%u\n", 
           header.cap, header.rid, header.n);
    
    TEST_PASS();
    return 1;
}

/**
 * Test 2: Key-Value Pair Structure (kv32_t)
 * Verify 8-byte KV pair layout
 */
int test_kv32() {
    TEST_START("test_kv32 - Key-Value Pair Structure");
    
    // Test structure size
    ASSERT_EQ(sizeof(kv32_t), 8, "KV pair size must be 8 bytes");
    
    // Test macro construction
    kv32_t kv1 = KV(0x1001, 0x2002);
    kv32_t kv2 = KV(0x3003, 0x4004);
    
    ASSERT_EQ(kv1.k, 0x1001, "KV1 key mismatch");
    ASSERT_EQ(kv1.v, 0x2002, "KV1 value mismatch");
    ASSERT_EQ(kv2.k, 0x3003, "KV2 key mismatch");
    ASSERT_EQ(kv2.v, 0x4004, "KV2 value mismatch");
    
    // Test BYTES_KV macro
    ASSERT_EQ(BYTES_KV(3), 24, "BYTES_KV calculation incorrect");
    
    printf("  - KV pair size: %zu bytes\n", sizeof(kv32_t));
    printf("  - kv1: k=%08x v=%08x\n", kv1.k, kv1.v);
    printf("  - kv2: k=%08x v=%08x\n", kv2.k, kv2.v);
    printf("  - BYTES_KV(3) = %zu bytes\n", (size_t)BYTES_KV(3));
    
    TEST_PASS();
    return 1;
}

/**
 * Test 3: Budget Structure (bud_t)
 * Verify 12-byte budget layout
 */
int test_bud() {
    TEST_START("test_bud - Budget Structure");
    
    // Test structure size
    ASSERT_EQ(sizeof(bud_t), 12, "Budget size must be 12 bytes");
    
    // Test macro construction
    bud_t budget = BUD(1, 1000000, 50000);
    
    ASSERT_EQ(budget.mode, 1, "Budget mode mismatch");
    ASSERT_EQ(budget.cap_credits, 1000000, "Capacity mismatch");
    ASSERT_EQ(budget.used_credits, 50000, "Used credits mismatch");
    
    // Test budget calculation
    uint32_t remaining = budget.cap_credits - budget.used_credits;
    ASSERT_EQ(remaining, 950000, "Remaining credits calculation incorrect");
    
    printf("  - Budget size: %zu bytes\n", sizeof(bud_t));
    printf("  - mode=%u cap=%u used=%u\n", 
           budget.mode, budget.cap_credits, budget.used_credits);
    printf("  - remaining=%u (%.1f%%)\n", 
           remaining, (float)remaining / budget.cap_credits * 100);
    
    TEST_PASS();
    return 1;
}

/**
 * Test 4: Full Message Assembly
 * Test complete message with header + KV payload
 */
int test_full_message() {
    TEST_START("test_full_message - Complete Message Assembly");
    
    // Create message with 3 KV pairs
    kv32_t kvs[3] = {
        KV(0x1001, 0x2002),
        KV(0x3003, 0x4004),
        KV(0x5005, 0x6006)
    };
    
    uint32_t payload_size = BYTES_KV(3);
    wh16_t header = WH(M_UPSERT, K_MCP, ANN_MCP, CAP_STANDARD, 
                       RID_USER_MIN, payload_size);
    
    // Calculate total message size
    uint32_t total_size = MSG_SIZE(payload_size);
    ASSERT_EQ(total_size, 16 + 24, "Message size calculation incorrect");
    
    // Allocate message buffer
    uint8_t *msg = (uint8_t *)malloc(total_size);
    ASSERT_TRUE(msg != NULL, "Memory allocation failed");
    
    // Assemble message
    memcpy(msg, &header, sizeof(wh16_t));
    memcpy(msg + sizeof(wh16_t), kvs, payload_size);
    
    // Verify message assembly
    wh16_t *read_header = (wh16_t *)msg;
    ASSERT_EQ(read_header->mt, M_UPSERT, "Read header mt mismatch");
    ASSERT_EQ(read_header->n, payload_size, "Read header payload size mismatch");
    
    kv32_t *read_kvs = (kv32_t *)(msg + sizeof(wh16_t));
    ASSERT_EQ(read_kvs[0].k, 0x1001, "Read KV0 key mismatch");
    ASSERT_EQ(read_kvs[1].v, 0x4004, "Read KV1 value mismatch");
    ASSERT_EQ(read_kvs[2].k, 0x5005, "Read KV2 key mismatch");
    
    printf("  - Total message size: %u bytes\n", total_size);
    printf("  - Header: %zu bytes\n", sizeof(wh16_t));
    printf("  - Payload: %u bytes (%d KV pairs)\n", payload_size, 3);
    printf("  - Message assembled and verified successfully\n");
    
    free(msg);
    TEST_PASS();
    return 1;
}

/**
 * Test 5: Annotation Bits
 * Test permission flags and combined patterns
 */
int test_annotation_bits() {
    TEST_START("test_annotation_bits - Permission Flags");
    
    // Test individual bits
    uint8_t ann_read = T_R;
    
    ASSERT_TRUE(HAS_READ(ann_read), "Read flag not detected");
    ASSERT_TRUE(!HAS_WRITE(ann_read), "False write detection");
    
    // Test combined patterns
    uint8_t ann_rw = ANN_RW;
    ASSERT_TRUE(HAS_READ(ann_rw), "RW pattern missing read");
    ASSERT_TRUE(HAS_WRITE(ann_rw), "RW pattern missing write");
    ASSERT_TRUE(!HAS_DELETE(ann_rw), "RW pattern has unexpected delete");
    
    uint8_t ann_mcp = ANN_MCP;
    ASSERT_TRUE(HAS_READ(ann_mcp), "MCP pattern missing read");
    ASSERT_TRUE(HAS_WRITE(ann_mcp), "MCP pattern missing write");
    ASSERT_TRUE(HAS_DELETE(ann_mcp), "MCP pattern missing delete");
    
    uint8_t ann_full = ANN_FULL;
    ASSERT_TRUE(HAS_READ(ann_full), "Full pattern missing read");
    ASSERT_TRUE(HAS_WRITE(ann_full), "Full pattern missing write");
    ASSERT_TRUE(HAS_DELETE(ann_full), "Full pattern missing delete");
    ASSERT_EQ(ann_full & T_X, T_X, "Full pattern missing execute");
    
    printf("  - T_R=%02x T_W=%02x T_D=%02x T_X=%02x\n", T_R, T_W, T_D, T_X);
    printf("  - ANN_RO=%02x ANN_RW=%02x ANN_MCP=%02x ANN_FULL=%02x\n",
           ANN_RO, ANN_RW, ANN_MCP, ANN_FULL);
    printf("  - All permission checks passed\n");
    
    TEST_PASS();
    return 1;
}

/**
 * Test 6: Record ID Ranges
 * Test RID validation and range checks
 */
int test_id_ranges() {
    TEST_START("test_id_ranges - Record ID Ranges");
    
    // Test system range
    uint32_t rid_sys = RID_SYSTEM_MIN;
    ASSERT_TRUE(RID_IS_VALID(rid_sys), "System RID not valid");
    ASSERT_TRUE(RID_IS_SYSTEM(rid_sys), "System RID not detected");
    ASSERT_TRUE(!RID_IS_USER(rid_sys), "System RID incorrectly marked as user");
    
    // Test user range
    uint32_t rid_user = RID_USER_MIN;
    ASSERT_TRUE(RID_IS_VALID(rid_user), "User RID not valid");
    ASSERT_TRUE(RID_IS_USER(rid_user), "User RID not detected");
    ASSERT_TRUE(!RID_IS_SYSTEM(rid_user), "User RID incorrectly marked as system");
    
    // Test snapshot range
    uint32_t rid_snapshot = RID_SNAPSHOT_MIN;
    ASSERT_TRUE(RID_IS_VALID(rid_snapshot), "Snapshot RID not valid");
    
    // Test temp range
    uint32_t rid_temp = RID_TEMP_MIN;
    ASSERT_TRUE(RID_IS_VALID(rid_temp), "Temp RID not valid");
    
    // Test boundary
    uint32_t rid_invalid = RID_TEMP_MAX + 1;
    ASSERT_TRUE(!RID_IS_VALID(rid_invalid), "Invalid RID incorrectly marked valid");
    
    printf("  - System range: 0x%08x - 0x%08x\n", RID_SYSTEM_MIN, RID_SYSTEM_MAX);
    printf("  - User range:   0x%08x - 0x%08x\n", RID_USER_MIN, RID_USER_MAX);
    printf("  - Snapshot range: 0x%08x - 0x%08x\n", RID_SNAPSHOT_MIN, RID_SNAPSHOT_MAX);
    printf("  - Temp range:   0x%08x - 0x%08x\n", RID_TEMP_MIN, RID_TEMP_MAX);
    printf("  - All range validations passed\n");
    
    TEST_PASS();
    return 1;
}

/**
 * Test 7: Message Type Constants
 * Verify all message type values
 */
int test_message_types() {
    TEST_START("test_message_types - Message Type Constants");
    
    ASSERT_EQ(M_PING, 0x00, "M_PING value incorrect");
    ASSERT_EQ(M_PONG, 0x01, "M_PONG value incorrect");
    ASSERT_EQ(M_UPSERT, 0x02, "M_UPSERT value incorrect");
    ASSERT_EQ(M_QUERY, 0x03, "M_QUERY value incorrect");
    ASSERT_EQ(M_DELETE, 0x04, "M_DELETE value incorrect");
    ASSERT_EQ(M_SNAPSHOT, 0x05, "M_SNAPSHOT value incorrect");
    ASSERT_EQ(M_RESTORE, 0x06, "M_RESTORE value incorrect");
    ASSERT_EQ(M_SYNC, 0x07, "M_SYNC value incorrect");
    
    printf("  - M_PING=%02x M_PONG=%02x M_UPSERT=%02x M_QUERY=%02x\n",
           M_PING, M_PONG, M_UPSERT, M_QUERY);
    printf("  - M_DELETE=%02x M_SNAPSHOT=%02x M_RESTORE=%02x M_SYNC=%02x\n",
           M_DELETE, M_SNAPSHOT, M_RESTORE, M_SYNC);
    printf("  - All message types verified\n");
    
    TEST_PASS();
    return 1;
}

/**
 * Test 8: Capability Flags
 * Test capability bitmap patterns
 */
int test_capabilities() {
    TEST_START("test_capabilities - Capability Flags");
    
    // Test individual capabilities
    uint32_t cap_tools = P_TOOLS;
    uint32_t cap_apps = P_APPS;
    
    ASSERT_EQ(cap_tools, 0x10000000, "P_TOOLS value incorrect");
    ASSERT_EQ(cap_apps, 0x20000000, "P_APPS value incorrect");
    
    // Test combined capabilities
    uint32_t cap_standard = CAP_STANDARD;
    ASSERT_TRUE((cap_standard & P_TOOLS) != 0, "CAP_STANDARD missing P_TOOLS");
    ASSERT_TRUE((cap_standard & P_APPS) != 0, "CAP_STANDARD missing P_APPS");
    
    uint32_t cap_extended = CAP_EXTENDED;
    ASSERT_TRUE((cap_extended & P_TOOLS) != 0, "CAP_EXTENDED missing P_TOOLS");
    ASSERT_TRUE((cap_extended & P_APPS) != 0, "CAP_EXTENDED missing P_APPS");
    ASSERT_TRUE((cap_extended & P_FILES) != 0, "CAP_EXTENDED missing P_FILES");
    
    printf("  - P_TOOLS=%08x P_APPS=%08x P_FILES=%08x\n", P_TOOLS, P_APPS, P_FILES);
    printf("  - CAP_STANDARD=%08x CAP_EXTENDED=%08x\n", CAP_STANDARD, CAP_EXTENDED);
    printf("  - All capability checks passed\n");
    
    TEST_PASS();
    return 1;
}

// ============================================================================
// Test Runner
// ============================================================================

int main(void) {
    printf("==========================================================\n");
    printf("PD_AI Wire Protocol Test Suite\n");
    printf("==========================================================\n");
    
    // Run all tests
    test_wh16();
    test_kv32();
    test_bud();
    test_full_message();
    test_annotation_bits();
    test_id_ranges();
    test_message_types();
    test_capabilities();
    
    // Print summary
    printf("\n==========================================================\n");
    printf("Test Summary\n");
    printf("==========================================================\n");
    printf("Tests run:    %d\n", tests_run);
    printf("Tests passed: %d\n", tests_passed);
    printf("Tests failed: %d\n", tests_run - tests_passed);
    
    if (tests_passed == tests_run) {
        printf("\n✓✓✓ ALL TESTS PASSED ✓✓✓\n");
        return 0;
    } else {
        printf("\n✗✗✗ SOME TESTS FAILED ✗✗✗\n");
        return 1;
    }
}

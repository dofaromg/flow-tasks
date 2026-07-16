# MRL Bridge Neural Link Integration Guide

## Module Information

- **Module ID**: `Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1`
- **Origin Signature**: MrLiouWord
- **Original Authors**: Anthropic (Roo Code / Claude Code Extension)
- **Integration By**: MrLiouWord
- **Version**: 1.0.0
- **Status**: INITIALIZED_AWAITING_DL580_DEPLOYMENT
- **Created**: 2026-06-26T16:42:08Z

## Purpose

Bidirectional communication bridge between:
- VSCode Extension (local)
- Web Application (middle tier)
- DL580 Windows Runtime (remote)

Enables real-time task communication, event streaming, and command orchestration across distributed environments using WebSocket (Socket.IO) protocol.

## Architecture

### Components

1. **BridgeOrchestrator** (356 lines)
   - Type: Orchestrator
   - Role: Central coordinator for WebSocket connections and channels
   - Manages: ExtensionChannel, TaskChannel lifecycle
   - Connection States: CONNECTING, CONNECTED, RETRYING, DISCONNECTED, FAILED

2. **SocketTransport** (282 lines)
   - Type: Transport Layer
   - Role: Manages WebSocket connection lifecycle and reconnection logic
   - Protocol: Socket.IO v4.x
   - Retry: Infinite attempts with exponential backoff (1s-30s, multiplier 2)
   - Timeout: 2000ms for initial connection

3. **TaskChannel** (242 lines)
   - Type: Communication Channel
   - Role: Handles task-level communication and subscriptions
   - Events: Message, TaskModeSwitched, TaskInteractive
   - Mapping: RooCodeEventName → TaskBridgeEventName

4. **BaseChannel** (143 lines)
   - Type: Abstract Base Class
   - Role: Common functionality for all communication channels
   - Pattern: Template method (handleCommand pattern)
   - Properties: instanceId, appProperties, gitProperties, isCloudAgent

5. **index.ts** (7 lines)
   - Type: Module Exports
   - Exports: BridgeOrchestrator, SocketTransport, BaseChannel, TaskChannel

### Transport Configuration

```json
{
  "protocol": "WebSocket",
  "library": "Socket.IO",
  "version": "4.x",
  "endpoints": {
    "dl580_bridge_api": "bridge.mrliouword.com/v3.1.0",
    "local_ws_server": "localhost:8099"
  }
}
```

### Authentication

- **Method**: x-api-key header
- **Source**: Environment variable `MRL_BRIDGE_TOKEN`
- **Scope**: DL580 bridge API access

### Reconnection Policy

- **Enabled**: Yes
- **Max Attempts**: Infinity
- **Initial Delay**: 1000ms
- **Max Delay**: 30000ms
- **Backoff Multiplier**: 2x

## Deployment

### System Requirements

- **Node.js**: >= 18.0.0
- **NPM Packages**:
  - socket.io-client (4.x)
  - @roo-code/types

- **Runtime**: Windows (DL580)
- **Target Path**: `D:\MRL_Mother\bridge_modules\Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1`

### Installation Steps

1. **Validate Module**
   ```powershell
   .\scripts\install.ps1 -ModuleRoot "D:\MRL_Mother\bridge_modules\Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1"
   ```
   - Checks directory structure
   - Validates source files (5 required)
   - Verifies JSON configuration
   - Confirms dependencies

2. **Verify Deployment**
   ```powershell
   .\scripts\verify.ps1 -ModuleRoot "D:\MRL_Mother\bridge_modules\Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1"
   ```
   - Validates all components exist
   - Checks for placeholder-only files
   - Verifies configuration syntax
   - Generates verification report

3. **Create Package**
   ```powershell
   .\scripts\package.ps1 -ModuleRoot "D:\MRL_Mother\bridge_modules\Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1" `
                         -OutputDir "D:\MRL_Mother\packages"
   ```
   - Creates deployment zip archive
   - Generates package manifest
   - Ready for distribution to target DL580

### Environment Setup

Set the bridge token before deployment:

```powershell
# On DL580 target system
[Environment]::SetEnvironmentVariable("MRL_BRIDGE_TOKEN", "<api-key>", "User")
```

Or in Node.js environment:

```javascript
process.env.MRL_BRIDGE_TOKEN = process.env.MRL_BRIDGE_TOKEN || "<api-key>";
```

## Integration with MRL Mother Model

### Registry Entry

The module is registered in `runtime_bridge.json` under:

```json
{
  "bridge_modules": {
    "Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1": {
      "path": "D:\\MRL_Mother\\bridge_modules\\Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1",
      "version": "1.0.0",
      "type": "bridge_neural_link",
      "target_runtime": "DL580_Windows",
      "status": "initialized",
      "endpoints": {
        "api": "bridge.mrliouword.com/v3.1.0",
        "local": "localhost:8099"
      }
    }
  }
}
```

### Immutability Rules

This module follows ADDITIVE_ONLY integration pattern:

1. **NO_DELETE_SOURCE_FILES**: All original TypeScript files are preserved as-is
2. **NO_RENAME_ORIGINAL_COMPONENTS**: Component names unchanged from source
3. **PRESERVE_PROVENANCE**: Author/origin information maintained
4. **ADDITIVE_ONLY_INTEGRATION**: New features add to existing structure, no overwrites

## Usage

### Basic Connection

```typescript
import { BridgeOrchestrator } from "./src/BridgeOrchestrator";

const orchestrator = BridgeOrchestrator.getInstance({
  bridgeUrl: "bridge.mrliouword.com/v3.1.0",
  appProperties: { appName: "VsCodeBridge" },
  instanceId: "vscode-1"
});

await orchestrator.connect();
```

### Task Subscription

```typescript
const taskId = "task-123";

// Subscribe to task events
await orchestrator.subscribeToTask(taskId);

// Listen for task-specific events
orchestrator.on("taskEvent", (event) => {
  console.log("Task event:", event);
});

// Unsubscribe when done
await orchestrator.unsubscribeFromTask(taskId);
```

### Event Handling

The bridge supports three task-level events:

- **Message**: Text communication between nodes
- **TaskModeSwitched**: Task mode/state changes
- **TaskInteractive**: Interactive user input/feedback

## Troubleshooting

### Connection Failures

1. **Check environment variable**:
   ```powershell
   [Environment]::GetEnvironmentVariable("MRL_BRIDGE_TOKEN", "User")
   ```

2. **Verify endpoint accessibility**:
   ```powershell
   Test-NetConnection -ComputerName bridge.mrliouword.com -Port 443
   ```

3. **Check Node.js version**:
   ```powershell
   node --version  # Should be >= 18.0.0
   ```

### DNS/Network Issues

- Verify DL580 can reach `bridge.mrliouword.com`
- Check firewall rules for outbound WebSocket (port 443)
- Confirm proxy settings if applicable

### Socket.IO Connection Errors

1. Verify Socket.IO client is installed: `npm list socket.io-client`
2. Check protocol compatibility: Socket.IO 4.x required
3. Validate token format and expiration

## Verification Output

After running `verify.ps1`, check the generated report:

```
evidence/verify_result.json
```

Expected fields:

```json
{
  "verification_timestamp": "2026-06-28T...",
  "module_id": "Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1",
  "pass_count": 12,
  "fail_count": 0,
  "findings": [...]
}
```

Success criteria: `fail_count = 0` and all source files validated.

## Support & Contact

- **Origin**: Anthropic (Roo Code / Claude Code Extension)
- **Integration**: MrLiouWord
- **Module Location**: `/home/user/MRL_AI_SYSTEM/MRL_MotherModel/bridge_modules/Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1`
- **Repository**: dofaromg/MRL_AI_SYSTEM

## Changelog

### v1.0.0 (2026-06-26)

- **Added**: Initial bridge module with 5 TypeScript components
- **Added**: DL580 Windows runtime configuration
- **Added**: PowerShell deployment scripts (install, verify, package)
- **Added**: Socket.IO WebSocket transport with infinite reconnection
- **Added**: Task-level event mapping and channel subscriptions
- **Status**: Ready for DL580 deployment validation

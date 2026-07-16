"use strict";
// MRL_Orchestration_PIDBridge — persistent loop supervision + runtime restart orchestration
// origin_signature=MrLiouWord
// 監督本層自行 spawn 的 runtime 程序；死亡且可恢復時，重啟並更新 recovery chain。
// 僅作用於本層 spawn / 註冊的 PID，不對任意系統程序動手。

const { spawn } = require("child_process");

// 長駐占位程序：模擬一個常駐 runtime（實務上換成真正的 runtime 進入點）。
const KEEPALIVE = ["-e", "setInterval(function(){}, 1 << 30)"];

class OrchestrationPIDBridge {
  constructor(pidScopeCore, runtimeRecovery, spawnArgs) {
    this.core = pidScopeCore;
    this.recovery = runtimeRecovery;
    this.procs = new Map(); // runtime_id -> ChildProcess
    this._args = spawnArgs || KEEPALIVE;
  }

  _spawn() { return spawn(process.execPath, this._args, { stdio: "ignore" }); }

  spawnRuntime(runtime_id, workflow_scope) {
    const child = this._spawn();
    this.procs.set(runtime_id, child);
    this.core.registerRuntime({ runtime_id, workflow_scope, pid: child.pid });
    return child.pid;
  }

  // 監督一次：存活則 noop；死亡則重啟（recovery），更新 PID 與 restart chain。
  superviseOnce(runtime_id) {
    const rec = this.core.owner(runtime_id);
    if (!rec) throw new Error("unknown runtime: " + runtime_id);
    if (this.core.isAlive(rec.pid)) return { action: "alive", pid: rec.pid };
    const old_pid = rec.pid;
    const child = this._spawn();
    this.procs.set(runtime_id, child);
    this.core.updatePid(runtime_id, child.pid);
    this.recovery.recordRestart(runtime_id, old_pid, child.pid);
    return { action: "restarted", old_pid, new_pid: child.pid };
  }

  stopAll() {
    for (const c of this.procs.values()) { try { c.kill("SIGKILL"); } catch (e) {} }
    this.procs.clear();
  }
}

module.exports = { OrchestrationPIDBridge };

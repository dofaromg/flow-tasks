"use strict";
// MRL_PIDScope_Acceptance — runnable acceptance for the Workflow Ownership layer
// origin_signature=MrLiouWord
// 本地驗收（local adapter）。正式 MRL_BaseWorld_DB_v1 接線待授權。
//
// 註：等待子程序死亡時使用 'exit' 事件（async）而非同步忙等，
//     否則同步迴圈會阻塞 event loop，被 SIGKILL 的子程序停在 zombie 狀態無法回收，
//     process.kill(pid,0) 仍會成功而誤判為存活。

const path = require("path");
const os = require("os");
const fs = require("fs");
const { once } = require("events");
const { spawn } = require("child_process");
const { createPIDScopeLayer } = require("../../MRL_Runtime/MRL_Workflow_PIDScope");

function assert(cond, msg) { if (!cond) throw new Error("assert failed: " + msg); }

const results = [];
async function test(name, fn) {
  try { await fn(); results.push([name, "PASS"]); console.log("PASS  " + name); }
  catch (e) { results.push([name, "FAIL", e.message]); console.log("FAIL  " + name + " -- " + e.message); }
}

(async function main() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "mrl_pidscope_acc_"));
  const L = createPIDScopeLayer({ dbTarget: { dir } });
  L.db.reset();
  const cleanupPids = [];

  await test("A. PID Ownership", function () {
    L.core.registerRuntime({ runtime_id: "MRL_Runtime_001", workflow_scope: "MRL_RuntimeScope", pid: process.pid });
    L.core.registerRuntime({ runtime_id: "MRL_Runtime_002", workflow_scope: "MRL_WorldScope", pid: process.pid });
    const all = L.core.all();
    assert(all.length === 2, "two runtimes registered");
    for (const r of all) assert(r.pid_owner && r.runtime_id && r.workflow_scope, "every runtime has owner");
    let threw = false;
    try { L.core.registerRuntime({ runtime_id: "anon" }); } catch (e) { threw = true; }
    assert(threw, "anonymous runtime rejected");
  });

  await test("B. Recovery (restart -> runtime structure field recoverable)", function () {
    L.structureField.addNode("MRL_Runtime_001", "MRL_RuntimeScope");
    L.structureField.addNode("MRL_Runtime_002", "MRL_WorldScope");
    L.structureField.addEdge("MRL_Runtime_001", "MRL_Runtime_002");
    const cp = L.recovery.checkpoint("before-mutate");
    L.structureField.addNode("MRL_Runtime_003", "MRL_ReplayScope");
    assert(L.structureField.nodes.size === 3, "structure field mutated to 3 nodes");
    L.recovery.restore(cp.checkpoint_id);
    assert(L.structureField.nodes.size === 2, "structure field restored to 2 nodes");
    assert(JSON.stringify(L.structureField.snapshot()) === JSON.stringify(cp.structureField), "structure field exact after restore");
  });

  await test("C. Replay exactness", function () {
    const expected = [];
    for (let i = 0; i < 10; i++) {
      const v = { i: i, tag: "particle_" + i };
      L.registry.trace("MRL_Runtime_001", "append", v);
      expected.push(v);
    }
    const replayed = L.registry.replay("MRL_Runtime_001");
    assert(JSON.stringify(replayed) === JSON.stringify(expected), "replay equals ordered persisted state");
  });

  await test("D. Scope Isolation", function () {
    const clean = L.isolation.check();
    assert(clean.length === 0, "clean: no contamination (got " + JSON.stringify(clean) + ")");
    L.core.registerRuntime({ runtime_id: "MRL_Runtime_001", workflow_scope: "MRL_WorldScope", pid: process.pid });
    const dirty = L.isolation.check();
    assert(dirty.some(function (x) { return x.type === "multi_scope"; }), "multi_scope contamination detected");
  });

  await test("E. Orphan Detection", async function () {
    const child = spawn(process.execPath, ["-e", "setTimeout(function(){}, 5000)"], { stdio: "ignore" });
    const opid = child.pid;
    L.core.registerRuntime({ runtime_id: "MRL_Runtime_orphan", workflow_scope: "MRL_RuntimeScope", pid: opid });
    child.kill("SIGKILL");
    await once(child, "exit"); // 等待回收，避免 zombie 誤判
    const orphans = L.core.listOrphans().map(function (r) { return r.runtime_id; });
    assert(orphans.indexOf("MRL_Runtime_orphan") !== -1, "orphan PID detected");
  });

  await test("F. Persistent Loop (runtime survives restart)", async function () {
    const pid1 = L.orchestrator.spawnRuntime("MRL_Runtime_loop", "MRL_RuntimeScope");
    cleanupPids.push(pid1);
    assert(L.core.isAlive(pid1), "runtime spawned and alive");
    const child1 = L.orchestrator.procs.get("MRL_Runtime_loop");
    process.kill(pid1, "SIGKILL");
    await once(child1, "exit"); // 等待回收
    const r = L.orchestrator.superviseOnce("MRL_Runtime_loop");
    assert(r.action === "restarted", "supervisor restarted the runtime");
    assert(L.core.isAlive(r.new_pid), "restarted runtime alive");
    cleanupPids.push(r.new_pid);
    assert(L.recovery.restartChain("MRL_Runtime_loop").length >= 1, "restart chain recorded");
  });

  L.orchestrator.stopAll();
  for (const p of cleanupPids) { try { process.kill(p, "SIGKILL"); } catch (e) {} }

  const failed = results.filter(function (r) { return r[1] === "FAIL"; });
  console.log("\n=== MRL_PIDScope_Acceptance (db: " + L.db.kind + ") ===");
  for (const r of results) console.log(r.join("  "));
  if (failed.length) { console.log("RESULT: BLOCKED (" + failed.length + " failing)"); process.exit(1); }
  console.log("RESULT: MRL_PIDSCOPE_ACCEPTANCE_PASS");
  process.exit(0);
})();

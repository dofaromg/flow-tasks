/**
 * particle-pvm v1.1.0 — 粒子虛擬機 (DL580 本地版)
 *
 * L4-Execution | 25 Opcodes | 5 Registers | 完整堆疊+記憶體
 * 端點: /execute /attention-loop /health /
 *
 * origin_signature: MrLiouWord
 * 怎麼過去就怎麼回來
 */

const VERSION = "1.1.0";

const OPCODES = [
  "NOP", "PUSH", "POP", "DUP", "SWAP",
  "LOAD", "STORE", "CLONE", "DELETE",
  "FOCUS", "SPREAD", "REWEIGHT", "CHECK",
  "LINK", "UNLINK", "TRAVERSE",
  "HASH", "DELTA", "MERGE",
  "CALL", "RET", "JMP", "JZ", "JNZ", "HALT"
];

const REGISTERS = ["PC", "SP", "FP", "HP", "ACC"];

class ParticleVM {
  constructor() {
    this.stack = [];
    this.memory = {};
    this.registers = { PC: 0, SP: 0, FP: 0, HP: 0, ACC: 0 };
    this.history = [];
    this.links = [];
    this.halted = false;
  }

  execute(program) {
    const results = [];
    this.halted = false;

    for (const instr of program) {
      if (this.halted) break;
      const result = this.step(instr);
      results.push(result);
    }

    return {
      results,
      state: {
        stack: [...this.stack],
        registers: { ...this.registers },
        memory: { ...this.memory },
        links: [...this.links],
        history_count: this.history.length,
        halted: this.halted
      }
    };
  }

  step(instr) {
    const op = (typeof instr === "string" ? instr : instr.op || instr.opcode || "NOP").toUpperCase();
    const args = typeof instr === "object" ? instr : {};
    const before = { stack: this.stack.length, acc: this.registers.ACC };

    this.history.push({ op, args, timestamp: Date.now() });
    this.registers.PC++;

    switch (op) {
      case "NOP": break;

      case "PUSH":
        this.stack.push(args.value ?? args.v ?? 0);
        this.registers.SP = this.stack.length;
        break;

      case "POP":
        this.registers.ACC = this.stack.pop() ?? 0;
        this.registers.SP = this.stack.length;
        break;

      case "DUP":
        if (this.stack.length > 0) this.stack.push(this.stack[this.stack.length - 1]);
        this.registers.SP = this.stack.length;
        break;

      case "SWAP": {
        const len = this.stack.length;
        if (len >= 2) [this.stack[len - 1], this.stack[len - 2]] = [this.stack[len - 2], this.stack[len - 1]];
        break;
      }

      case "LOAD":
        this.registers.ACC = this.memory[args.key || args.addr] ?? 0;
        break;

      case "STORE":
        this.memory[args.key || args.addr] = args.value ?? this.registers.ACC;
        this.registers.HP++;
        break;

      case "CLONE": {
        const src = args.key || args.from;
        const dst = args.to || `${src}_clone`;
        if (this.memory[src] !== undefined) {
          this.memory[dst] = JSON.parse(JSON.stringify(this.memory[src]));
        }
        break;
      }

      case "DELETE":
        delete this.memory[args.key || args.addr];
        break;

      case "FOCUS":
        this.registers.ACC = args.target ?? (this.stack.length > 0 ? this.stack[this.stack.length - 1] : 0);
        break;

      case "SPREAD": {
        const val = this.registers.ACC;
        const n = args.count || 3;
        for (let i = 0; i < n; i++) this.stack.push(val / n);
        this.registers.SP = this.stack.length;
        break;
      }

      case "REWEIGHT": {
        const factor = args.factor || 1.1;
        if (this.stack.length > 0) {
          this.stack[this.stack.length - 1] *= factor;
        }
        break;
      }

      case "CHECK": {
        const threshold = args.threshold || 0.7;
        const top = this.stack.length > 0 ? this.stack[this.stack.length - 1] : 0;
        this.registers.ACC = top >= threshold ? 1 : 0;
        break;
      }

      case "LINK":
        this.links.push({ from: args.from, to: args.to, type: args.type || "default" });
        break;

      case "UNLINK":
        this.links = this.links.filter(l => !(l.from === args.from && l.to === args.to));
        break;

      case "TRAVERSE": {
        const start = args.from;
        const connected = this.links.filter(l => l.from === start).map(l => l.to);
        this.registers.ACC = connected.length;
        this.stack.push(...connected);
        this.registers.SP = this.stack.length;
        break;
      }

      case "HASH": {
        const input = String(args.value ?? this.registers.ACC);
        let hash = 0;
        for (let i = 0; i < input.length; i++) {
          hash = ((hash << 5) - hash + input.charCodeAt(i)) | 0;
        }
        this.registers.ACC = Math.abs(hash);
        break;
      }

      case "DELTA": {
        const a = args.a ?? (this.stack.length >= 2 ? this.stack[this.stack.length - 2] : 0);
        const b = args.b ?? (this.stack.length >= 1 ? this.stack[this.stack.length - 1] : 0);
        this.registers.ACC = b - a;
        break;
      }

      case "MERGE": {
        const vals = this.stack.splice(-Math.min(args.count || 2, this.stack.length));
        const merged = vals.reduce((s, v) => s + (typeof v === "number" ? v : 0), 0);
        this.stack.push(merged);
        this.registers.SP = this.stack.length;
        this.registers.ACC = merged;
        break;
      }

      case "JMP":
        this.registers.PC = args.target ?? this.registers.PC;
        break;

      case "JZ":
        if (this.registers.ACC === 0) this.registers.PC = args.target ?? this.registers.PC;
        break;

      case "JNZ":
        if (this.registers.ACC !== 0) this.registers.PC = args.target ?? this.registers.PC;
        break;

      case "CALL":
        this.stack.push(this.registers.PC);
        this.registers.FP = this.registers.SP;
        this.registers.PC = args.target ?? this.registers.PC;
        break;

      case "RET": {
        const retAddr = this.stack.pop();
        if (typeof retAddr === "number") this.registers.PC = retAddr;
        this.registers.SP = this.stack.length;
        break;
      }

      case "HALT":
        this.halted = true;
        break;

      default:
        return { op, error: `Unknown opcode: ${op}` };
    }

    return {
      op,
      stack_size: this.stack.length,
      acc: this.registers.ACC,
      pc: this.registers.PC
    };
  }
}

const json = (data, status = 200) => new Response(JSON.stringify(data, null, 2), {
  status,
  headers: { "Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*", "X-Origin-Signature": "MrLiouWord" }
});

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
    }

    if (path === "/" || path === "") {
      return json({
        name: "particle-pvm", version: VERSION, layer: "L4",
        description: "粒子虛擬機 (Particle Virtual Machine)",
        features: ["粒子堆疊管理", "粒子記憶體", "注意力迴圈", "操作歷史追蹤", "可逆操作支援"],
        opcodes: OPCODES, registers: REGISTERS,
        endpoints: ["/execute", "/attention-loop"],
        origin_signature: "MrLiouWord", runtime: "DL580-local"
      });
    }

    if (path === "/health") {
      return json({ status: "healthy", name: "particle-pvm", version: VERSION, origin_signature: "MrLiouWord", runtime: "DL580-local", timestamp: new Date().toISOString() });
    }

    if (request.method !== "POST") return json({ error: "POST required" }, 405);

    let body;
    try { body = await request.json(); } catch { return json({ error: "invalid JSON" }, 400); }

    if (path === "/execute") {
      const program = body.program || body.instructions || [];
      if (!Array.isArray(program)) return json({ success: false, error: "program[] required" }, 400);
      const vm = new ParticleVM();
      const result = vm.execute(program);
      return json({ success: true, ...result, origin_signature: "MrLiouWord" });
    }

    if (path === "/attention-loop") {
      const particles = body.particles || [{ id: "p1", weight: 0.5 }, { id: "p2", weight: 0.5 }];
      const cycles = body.cycles || 5;
      const vm = new ParticleVM();

      // Run attention loop as PVM program
      const program = [];
      for (const p of particles) {
        program.push({ op: "PUSH", value: p.weight || 0 });
        program.push({ op: "STORE", key: p.id, value: p.weight || 0 });
      }
      for (let c = 0; c < cycles; c++) {
        program.push({ op: "FOCUS", target: particles[0]?.weight || 0 });
        program.push({ op: "CHECK", threshold: 0.7 });
        program.push({ op: "SPREAD", count: particles.length });
        program.push({ op: "REWEIGHT", factor: 1.05 });
      }

      const result = vm.execute(program);
      return json({ success: true, mode: "attention-loop", cycles, ...result, origin_signature: "MrLiouWord" });
    }

    return json({ error: "route not found", path }, 404);
  }
};

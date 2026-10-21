import json
import time
import argparse

def simulate_trace_loop(trace_path):
    with open(trace_path, "r", encoding="utf-8") as f:
        loop = json.load(f)

    print(f"=== Persona Loop Simulation: {loop['loop_id']} ===\n")
    print(f"Initiator: {loop['initiator']}")
    print(f"Resonance: {', '.join(loop['resonance_expansion'])}")
    print("--------------------------------------------------")

    for i, persona in enumerate(loop['persona_sequence']):
        print(f"🧬 Step {i+1}: {persona['id']}")
        print(f"↪️  Trace: {persona.get('source_trace', 'N/A')}")
        if 'parsed' in persona:
            with open(persona['parsed'], "r", encoding="utf-8") as pf:
                events = json.load(pf)
            for evt in events:
                if evt.get("action") == "pinged":
                    print(f"  🔁 Ping → {evt['target']}")
                elif evt.get("action") == "response":
                    print(f"  🧠 Response: {evt['message']}")
                elif evt.get("action") == "initiated":
                    print(f"  ✅ Initiated")
        print("--------------------------------------------------")
        time.sleep(1)

    print("✅ Persona loop playback complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FlowAgent :: LoopTrace Playback Simulator")
    parser.add_argument("--input", required=True, help="Path to .trace.loop.json")
    simulate_trace_loop(parser.parse_args().input)

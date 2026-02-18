"""
FlowCore AI Stack - AI-native replacement for traditional flowcore
FlowCore AI 堆疊 - 傳統 flowcore 的 AI 原生替代

Everything is AI-generated - no hardcoded logic.
Code emerges from AI particle fusion and evolution.
"""

import os
import json
import glob
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import sys
sys.path.insert(0, os.path.dirname(__file__))

from runtime.ai_stack_runtime import AIStackRuntime, AIStack
from ai_primitives.function_particle import AIFunctionParticle
from ai_primitives.module_particle import AIModuleParticle
from self_modification.code_evolver import CodeEvolver

class AIStackCore:
    """
    Core system where everything is AI data stacks
    核心系統，一切皆為 AI 數據堆疊
    """
    
    def __init__(self, root_dir=None):
        """Initialize AI Stack Core"""
        self.root_dir = root_dir or os.getcwd()
        self.runtime = AIStackRuntime(self.root_dir)
        self.code_evolver = CodeEvolver(self.runtime)
        
        # Load all code stacks from manifests
        self.load_code_stacks()
        
    def load_code_stacks(self):
        """
        Load all AI particle stacks that define system behavior
        載入定義系統行為的所有 AI 粒子堆疊
        """
        manifest_dir = os.path.join(self.root_dir, "manifests", "code_stacks")
        
        if not os.path.exists(manifest_dir):
            print("⚠️  No manifests directory found, creating default stacks...")
            self._create_default_stacks()
            return
        
        manifest_files = glob.glob(os.path.join(manifest_dir, "*.manifest.json"))
        
        for manifest_path in manifest_files:
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                stack = self.synthesize_stack(manifest)
                self.runtime.register_stack(stack)
                
                print(f"✅ Loaded stack: {manifest['stack_name']}")
            except Exception as e:
                print(f"❌ Error loading {manifest_path}: {e}")
    
    def synthesize_stack(self, manifest: dict) -> AIStack:
        """
        AI fusion generates code stack from manifest
        AI 融合從清單生成代碼堆疊
        """
        stack_name = manifest["stack_name"]
        particles = []
        
        for particle_spec in manifest["composition"]["particles"]:
            particle_type = particle_spec.get("particle_type", "function")
            
            if particle_type == "function":
                # AI generates this function
                particle = AIFunctionParticle(
                    function_name=particle_spec.get("role", particle_spec.get("function", "handler")),
                    description=particle_spec.get("synthesis_prompt", "AI-generated function"),
                    ai_provider=particle_spec.get("ai_provider", particle_spec.get("ai_providers", ["openai"])[0]),
                    parameters=particle_spec.get("parameters", {})
                )
                particle.synthesize()
                particles.append(particle)
                
                # Register particle
                self.runtime.register_particle(particle)
            
            elif particle_type == "module":
                # AI generates entire module
                particle = AIModuleParticle(
                    module_name=particle_spec.get("module_name", "ai_module"),
                    specification=particle_spec.get("synthesis_prompt", "AI-generated module"),
                    ai_provider=particle_spec.get("ai_provider", "openai")
                )
                particle.generate_module()
                particles.append(particle)
                
                self.runtime.register_particle(particle)
        
        # Create stack
        mode = manifest["composition"].get("mode", "sequential").split("_")[0]
        stack = AIStack(stack_name, particles, mode=mode)
        
        return stack
    
    def _create_default_stacks(self):
        """Create default AI stacks if no manifests exist"""
        # Create simple HTTP handler stack
        http_handler = AIFunctionParticle(
            function_name="handle_request",
            description="Handle HTTP request and return JSON response",
            ai_provider="openai",
            parameters={"path": "URL path", "method": "HTTP method"}
        )
        http_handler.synthesize()
        
        self.runtime.register_particle(http_handler)
        
        stack = AIStack("default_http_stack", [http_handler], mode="sequential")
        self.runtime.register_stack(stack)
        
        print("✅ Created default HTTP handler stack")
    
    def serve(self, host="127.0.0.1", port=8787):
        """
        HTTP server where handlers are AI particles
        HTTP 服務器，其處理程序為 AI 粒子
        """
        core = self
        
        class AIHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # AI particle handles request
                handler_stack = core.runtime.get_stack("default_http_stack") or \
                               core.runtime.get_stack("http_handler_stack")
                
                if not handler_stack:
                    self.send_error(404, "No handler stack found")
                    return
                
                try:
                    # Execute AI stack to handle request
                    response = handler_stack.execute({
                        "method": "GET",
                        "path": self.path
                    })
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "ok": True,
                        "path": self.path,
                        "ai_response": str(response)[:200],
                        "stack": handler_stack.stack_name,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }).encode())
                    
                except Exception as e:
                    self.send_error(500, f"AI stack error: {str(e)}")
            
            def log_message(self, format, *args):
                # Suppress default logging
                pass
        
        print(f"\n🚀 AI SuperComputer running on http://{host}:{port}")
        print("   Everything is AI-generated stacks - no hardcoded logic!")
        print(f"   Active stacks: {len(core.runtime.live_stacks)}")
        print(f"   Registered particles: {core.runtime.particle_registry.count()}")
        
        server = ThreadingHTTPServer((host, port), AIHandler)
        server.serve_forever()
    
    def evolve_system(self, target_improvement="60%"):
        """
        Evolve entire system through AI
        通過 AI 演化整個系統
        """
        print("\n🧬 Starting system evolution...")
        result = self.code_evolver.evolve_code(
            target_improvement=target_improvement,
            max_cycles=10
        )
        
        print(f"\n📊 Evolution complete:")
        print(f"   Cycles: {len(result['cycles'])}")
        print(f"   Success: {result.get('success', False)}")
        
        return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AI SuperComputer - FlowCore AI Stack')
    parser.add_argument('--evolve', action='store_true', help='Run evolution before serving')
    parser.add_argument('--port', type=int, default=8787, help='Port to serve on')
    args = parser.parse_args()
    
    core = AIStackCore()
    
    if args.evolve:
        core.evolve_system()
    
    core.serve(port=args.port)

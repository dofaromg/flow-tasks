#!/usr/bin/env python3
# MRLiou Particle Language Core - Demo and Test Runner

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from logic_pipeline import LogicPipeline
    from rebuild_fn import FunctionRestorer
    from logic_transformer import LogicTransformer
    from memory_archive_seed import MemoryArchiveSeed
    from particle_regressor import ParticleRegressor
    from fluin_dict_agent import FluinDictAgent
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def demo_basic_functionality():
    """示範基本功能"""
    print("=== MRLiou Particle Language Core Demo ===\n")
    
    # 1. 邏輯管線示範
    print("1. 邏輯管線執行:")
    pipeline = LogicPipeline()
    result = pipeline.simulate("Hello, MRLiou!")
    print(f"   輸入: {result['input']}")
    print(f"   步驟: {' → '.join(result['steps'])}")
    print(f"   結果: {result['result']}")
    print(f"   壓縮: {result['compressed']}\n")
    
    # 2. 壓縮還原示範
    print("2. 壓縮還原功能:")
    restorer = FunctionRestorer()
    compressed = "SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))"
    decompressed = restorer.decompress_fn(compressed)
    recompressed = restorer.compress_fn(decompressed)
    print(f"   原始壓縮: {compressed}")
    print(f"   解壓縮: {' → '.join(decompressed)}")
    print(f"   重新壓縮: {recompressed}")
    print(f"   驗證一致: {compressed == recompressed}\n")
    
    # 3. 邏輯轉化示範
    print("3. 邏輯轉化功能:")
    transformer = LogicTransformer()
    test_chain = ["structure", "mark", "store"]
    symbols = transformer.compress_to_symbols(test_chain)
    flpkg = transformer.compress_to_flpkg(test_chain)
    transformation_map = transformer.create_transformation_map(test_chain)
    print(f"   函數鏈: {' → '.join(test_chain)}")
    print(f"   符號表示: {symbols}")
    print(f"   FLPKG 格式: {flpkg}")
    print(f"   複雜度: {transformation_map['complexity']}\n")
    
    # 4. 檔案操作示範
    print("4. 檔案儲存功能:")
    
    # 儲存邏輯結果
    output_filename = pipeline.store_result("Demo Data", result['result'], "examples")
    print(f"   邏輯結果已儲存: {output_filename}")
    
    # 建立 FLPKG 封包
    flpkg_package = restorer.create_flpkg_package(
        ["structure", "mark", "flow", "recurse", "store"],
        {"demo": True, "version": "1.0"}
    )
    flpkg_file = restorer.save_flpkg(flpkg_package, "examples/demo_package")
    filename = pipeline.store_result("Demo Data", result['result'], "examples")
    print(f"   邏輯結果已儲存: {filename}")
    
    # 建立 FLPKG 封包
    package = restorer.create_flpkg_package(
        ["structure", "mark", "flow", "recurse", "store"],
        {"demo": True, "version": "1.0"}
    )
    flpkg_file = restorer.save_flpkg(package, "examples/demo_package")
    print(f"   FLPKG 封包已儲存: {flpkg_file}")
    
    # JSON 匯出
    json_export = transformer.export_to_json(["structure", "store"])
    json_file = "examples/demo_transform.json"
    with open(json_file, 'w', encoding='utf-8') as json_output_file:
        json.dump(json_export, json_output_file, ensure_ascii=False, indent=2)
    print(f"   JSON 匯出已儲存: {json_file}")
    
    # 5. 記憶封存種子示範
    print("\n5. 記憶封存種子功能:")
    archive = MemoryArchiveSeed()
    
    # 創建記憶種子
    seed_data = {
        "logic_result": result['result'],
        "compressed": result['compressed'],
        "timestamp": "demo_execution"
    }
    seed_result = archive.create_seed(
        particle_data=seed_data,
        metadata={"demo": True, "type": "test"},
        seed_name="demo_memory_seed"
    )
    print(f"   記憶種子已創建: {seed_result['seed_name']}")
    print(f"   種子檔案: {seed_result['seed_file']}")
    print(f"   校驗碼: {seed_result['checksum'][:16]}...")
    
    # 壓縮種子
    compressed_seed = archive.compress_seed("demo_memory_seed")
    print(f"   壓縮格式: {compressed_seed}")
    
    # 6. 粒子回溯器示範 (Mrlword.v1)
    print("\n6. 粒子回溯器功能 (MrLioū.Particle.Mrlword.v1):")
    regressor = ParticleRegressor()
    
    # 回歸計算
    p_k = 100.0
    n, eta = 2.0, 0.5
    p_k_minus_1 = regressor.regress_state(p_k, n, eta)
    print(f"   回歸計算: P_{{k}} = {p_k} → P_{{k-1}} = {p_k_minus_1}")
    
    # Growth/Regress 互補驗證
    initial = 50.0
    grown = regressor.growth_state(initial, n, eta)
    regressed = regressor.regress_state(grown, n, eta)
    print(f"   互補驗證: {initial} → Growth → {grown} → Regress → {regressed}")
    
    # 逆向邏輯鏈
    regress_sim = regressor.simulate("記憶資料")
    print(f"   逆向步驟: {' → '.join(regress_sim['backward_steps'])}")
    print(f"   壓縮格式: {regress_sim['compressed']}")
    
    # 7. Fluin Dict Agent 示範 (DictSeed.0003)
    print("\n7. Fluin Dict Agent 字典種子記憶快照 (DictSeed.0003):")
    dict_agent = FluinDictAgent()
    
    # Echo/Jump 融合
    dict_agent.create_echo("demo_echo", "粒子記憶測試")
    dict_agent.set_jump_point("start", 0)
    echo_result = dict_agent.trigger_echo("demo_echo")
    print(f"   Echo 觸發: {echo_result['content']} ({echo_result['symbol']})")
    
    # 字典種子
    seed_result = dict_agent.create_dict_seed(
        "demo_dict_seed",
        {"key": "value", "data": [1, 2, 3]},
        {"purpose": "demo"}
    )
    print(f"   字典種子: {seed_result['seed_id']} (Core ⟁{seed_result['core_index']})")
    
    # 人格註冊與展開
    dict_agent.register_persona("demo_persona", "Demo Agent", ["helpful", "precise"])
    persona = dict_agent.expand_persona("demo_persona")
    print(f"   人格展開: {persona['persona']['name']} ({persona['symbol']})")
    
    # 粒子符號輸出
    print(f"   狀態符號:\n{dict_agent.compress_to_particle_notation()}")
    
    print("\n=== Demo 完成 ===")


    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_export, f, ensure_ascii=False, indent=2)
    print(f"   JSON 匯出已儲存: {json_file}")
    
    print("\n=== Demo 完成 ===")

def run_performance_test():
    """執行效能測試"""
    print("\n=== 效能測試 ===")
    import time
    
    pipeline = LogicPipeline()
    transformer = LogicTransformer()
    
    # 測試大量模擬
    start_time = time.time()
    for i in range(100):
        pipeline.simulate(f"test_data_{i}")
    simulation_time = time.time() - start_time
    print(f"100次邏輯模擬耗時: {simulation_time:.3f}秒")
    
    # 測試壓縮轉換
    start_time = time.time()
    test_chains = [
        ["structure", "store"],
        ["structure", "mark", "flow", "store"],
        ["structure", "mark", "flow", "recurse", "store"]
    ]
    for i in range(50):
        for chain in test_chains:
            transformer.create_transformation_map(chain)
    transform_time = time.time() - start_time
    print(f"150次轉換操作耗時: {transform_time:.3f}秒")

def show_system_info():
    """顯示系統資訊"""
    print("\n=== 系統資訊 ===")
    
    # 載入配置
    config_path = "config/core_config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"系統名稱: {config['core_config']['name']}")
        print(f"版本: {config['core_config']['version']}")
        print(f"預設步驟: {' → '.join(config['function_chain']['default_steps'])}")
    
    # 檢查範例檔案
    examples_dir = "examples"
    if os.path.exists(examples_dir):
        files = os.listdir(examples_dir)
        print(f"範例檔案數量: {len(files)}")
        for file in files:
            print(f"  - {file}")
    
    print(f"Python 版本: {sys.version}")

def main():
    """主函數"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "demo":
            demo_basic_functionality()
        elif command == "performance":
            run_performance_test()
        elif command == "info":
            show_system_info()
        elif command == "all":
            demo_basic_functionality()
            run_performance_test()
            show_system_info()
        else:
            print("可用指令: demo, performance, info, all")
    else:
        print("MRLiou Particle Language Core Test Runner")
        print("使用方式: python demo.py [command]")
        print("可用指令:")
        print("  demo        - 示範基本功能")
        print("  performance - 執行效能測試")
        print("  info        - 顯示系統資訊")
        print("  all         - 執行所有測試")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Quick Chess Model Testing - Tests top 3 models
"""

import subprocess
import json
import os
from pathlib import Path
import time
import yaml

# Top priority models based on analysis
QUICK_TEST_CONFIGS = [
    {
        "name": "GPT-4o-mini",
        "provider": "OpenAI",
        "model": "gpt-4o-mini",
        "temperature": 0.6,
        "reason": "Proven performer in initial tests"
    },
    {
        "name": "DeepSeek-R1",
        "provider": "OpenRouter",
        "model": "deepseek/deepseek-r1-0528",
        "temperature": 0.6,
        "reason": "Reasoning model, best for strategy"
    },
    {
        "name": "DeepSeek-Chat-v3.1",
        "provider": "OpenRouter",
        "model": "deepseek/deepseek-chat-v3.1",
        "temperature": 0.7,
        "reason": "Fast and strong general model"
    },
]

OPTIMIZED_PROMPTS = {
    "system_prompt": """You are an expert chess player. Your goal: win by making strategic, legal moves.

CRITICAL RULES:
1. Output format: [e2e4] (UCI in square brackets)
2. Choose ONLY from the valid moves list
3. Control center, develop pieces, protect king
4. Think ahead: consider opponent responses

Always end with your move in [UCI] format.""",

    "step_wise_prompt": """🎯 CHESS POSITION

Role: {role}

BOARD:
{board}

PIECES:
{piece_positions}

LEGAL MOVES:
{valid_moves}

HISTORY:
{past_up_to_five_moves}

ANALYSIS:
1. Threats? 2. Opportunities? 3. King safe? 4. Best move from legal list?

REMEMBER: lowercase=Black, UPPERCASE=White

[Your reasoning]
Final: [move]"""
}

def create_config(test_cfg):
    config = {
        "game": {"num_players": 2, "stop_after": 50},  # Shorter for quick test
        "agent0": {
            "model": {
                "provider": test_cfg["provider"],
                "name": test_cfg["model"],
                "params": {"temperature": test_cfg["temperature"]}
            },
            "prompts": OPTIMIZED_PROMPTS
        },
        "agent1": {
            "model": {
                "provider": "OpenRouter",
                "model": "deepseek/deepseek-chat-v3.1",
                "params": {"temperature": 0.7}
            },
            "prompts": {
                "system_prompt": "You are a chess player. Make legal moves.",
                "step_wise_prompt": "Role: {role}\nBoard: {board}\nMoves: {valid_moves}\nHistory: {past_up_to_five_moves}\n\nYour move: [move]"
            }
        }
    }

    with open("config.yml", 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def run_quick_test(cfg):
    print(f"\n{'='*70}")
    print(f"🎮 Testing: {cfg['name']}")
    print(f"   Model: {cfg['model']}")
    print(f"   Reason: {cfg['reason']}")
    print(f"{'='*70}")

    create_config(cfg)

    start = time.time()
    try:
        result = subprocess.run(
            ["uv", "run", "regular_chess.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout
        )
        elapsed = time.time() - start

        # Find latest results
        results_dir = Path("Results")
        matches = sorted(results_dir.glob("*/*"), key=os.path.getmtime, reverse=True)

        if matches:
            latest = matches[0]
            log_file = latest / "log.txt"

            invalid_moves = 0
            if log_file.exists():
                with open(log_file) as f:
                    log_content = f.read()
                    invalid_moves = log_content.count("Random fallback")

            game_info_file = latest / "game_info.json"
            winner = "Unknown"
            if game_info_file.exists():
                with open(game_info_file) as f:
                    game_info = json.load(f)
                    if "winner" in game_info:
                        winner = game_info["winner"]

            return {
                "name": cfg["name"],
                "model": cfg["model"],
                "success": True,
                "time": elapsed,
                "invalid_moves": invalid_moves,
                "winner": winner,
                "log": str(log_file)
            }

        return {"name": cfg["name"], "success": False, "error": "No results"}

    except subprocess.TimeoutExpired:
        return {"name": cfg["name"], "success": False, "error": "Timeout"}
    except Exception as e:
        return {"name": cfg["name"], "success": False, "error": str(e)}

def main():
    print("⚡ QUICK MODEL TESTING - Top 3 Models")
    print("=" * 70)

    results = []
    for i, cfg in enumerate(QUICK_TEST_CONFIGS, 1):
        print(f"\n📊 Test {i}/{len(QUICK_TEST_CONFIGS)}")
        result = run_quick_test(cfg)
        results.append(result)

        if result["success"]:
            print(f"✅ Success! Time: {result['time']:.1f}s")
            print(f"   Invalid moves: {result['invalid_moves']}")
            print(f"   Winner: {result.get('winner', 'N/A')}")
        else:
            print(f"❌ Failed: {result.get('error')}")

        if i < len(QUICK_TEST_CONFIGS):
            time.sleep(3)

    # Summary
    print("\n\n" + "=" * 70)
    print("📊 QUICK TEST RESULTS")
    print("=" * 70)

    successful = [r for r in results if r["success"]]
    if successful:
        successful.sort(key=lambda x: (x["invalid_moves"], x["time"]))

        print("\n🏆 RANKED RESULTS:\n")
        for i, r in enumerate(successful, 1):
            print(f"{i}. {r['name']}")
            print(f"   Invalid moves: {r['invalid_moves']} | Time: {r['time']:.1f}s")
            print(f"   Winner: {r.get('winner', 'N/A')}")
            print()

        best = successful[0]
        print("\n" + "🎯" * 35)
        print(f"🏆 BEST PERFORMER: {best['name']}")
        print(f"   Model: {best['model']}")
        print(f"   Invalid moves: {best['invalid_moves']}")
        print(f"   Time: {best['time']:.1f}s")
        print("🎯" * 35)

        # Create final config
        for cfg in QUICK_TEST_CONFIGS:
            if cfg["name"] == best["name"]:
                create_full_config(cfg)
                print(f"\n✅ Final config.yml created with {best['name']}")
                print("   Ready for submission!")
                break

    # Save results
    with open("quick_test_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    print("\n📁 Results saved to: quick_test_results.json")

def create_full_config(cfg):
    """Create full 100-step config for submission"""
    config = {
        "game": {"num_players": 2, "stop_after": 100},
        "agent0": {
            "model": {
                "provider": cfg["provider"],
                "name": cfg["model"],
                "params": {"temperature": cfg["temperature"]}
            },
            "prompts": OPTIMIZED_PROMPTS
        },
        "agent1": {  # Dummy agent for structure
            "model": {
                "provider": "OpenRouter",
                "model": "deepseek/deepseek-chat-v3.1",
                "params": {"temperature": 0.7}
            },
            "prompts": {
                "system_prompt": "You are a chess player.",
                "step_wise_prompt": "Role: {role}\nMoves: {valid_moves}\nMove: [move]"
            }
        }
    }

    with open("config.yml", 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    main()

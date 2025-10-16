#!/usr/bin/env python3
"""
Comprehensive Chess Model Testing
Tests all available models and finds the best performer
"""

import subprocess
import json
import os
from pathlib import Path
import time
import yaml

# Test configurations for all approved models
TEST_CONFIGS = [
    {
        "name": "DeepSeek-R1-0528",
        "provider": "OpenRouter",
        "model": "deepseek/deepseek-r1-0528",
        "temperature": 0.6,
        "priority": 1  # High priority - reasoning model
    },
    {
        "name": "DeepSeek-Chat-v3.1",
        "provider": "OpenRouter",
        "model": "deepseek/deepseek-chat-v3.1",
        "temperature": 0.7,
        "priority": 2
    },
    {
        "name": "GPT-4o-mini",
        "provider": "OpenAI",
        "model": "gpt-4o-mini",
        "temperature": 0.6,
        "priority": 1  # High priority - proven performer
    },
    {
        "name": "Gemini-2.5-Flash-Preview",
        "provider": "OpenRouter",
        "model": "google/gemini-2.5-flash-preview-09-2025",
        "temperature": 0.7,
        "priority": 2
    },
    {
        "name": "Gemini-2.5-Flash",
        "provider": "OpenRouter",
        "model": "google/gemini-2.5-flash",
        "temperature": 0.7,
        "priority": 3
    },
    {
        "name": "Qwen3-235b",
        "provider": "OpenRouter",
        "model": "qwen/qwen3-235b-a22b-2507",
        "temperature": 0.7,
        "priority": 3
    },
    {
        "name": "Grok-4-Fast",
        "provider": "OpenRouter",
        "model": "x-ai/grok-4-fast",
        "temperature": 0.7,
        "priority": 3
    },
]

# Optimized prompt template
OPTIMIZED_SYSTEM_PROMPT = """You are an expert chess player competing in a tournament. Your goal is to win by making strategic, legal moves.

Key principles:
1. Always output moves in UCI format within square brackets: [e2e4]
2. Control the center (e4, d4, e5, d5)
3. Develop pieces early (knights before bishops)
4. Protect your king (consider castling)
5. Think ahead: consider opponent's responses
6. Only make moves from the valid moves list provided

Format: Always end with your move in [UCI] format on the last line."""

OPTIMIZED_STEP_PROMPT = """[CHESS GAME - Move Analysis]

You are playing as {role}.

=== CURRENT BOARD ===
{board}

=== PIECE POSITIONS ===
{piece_positions}

=== YOUR LEGAL MOVES ===
{valid_moves}

=== RECENT GAME HISTORY ===
{past_up_to_five_moves}

=== YOUR TASK ===
Analyze the position step-by-step:

1. ASSESS THREATS: What is my opponent threatening?
2. IDENTIFY OPPORTUNITIES: Can I capture pieces, control center, or improve position?
3. CONSIDER STRATEGY: Am I developing pieces? Is my king safe?
4. EVALUATE OPTIONS: Compare 2-3 best moves from the legal moves list
5. CHOOSE MOVE: Select the best move

IMPORTANT:
- You MUST choose from the legal moves list above
- Small letters (p, n, b, r, q, k) = Black pieces
- Capital letters (P, N, B, R, Q, K) = White pieces

Output format:
[Your reasoning]

Final move: [UCI_move_in_brackets]"""


def create_test_config(test_config, output_file="config.yml"):
    """Create a config.yml for testing a specific model"""
    config = {
        "game": {
            "num_players": 2,
            "stop_after": 100
        },
        "agent0": {
            "model": {
                "provider": test_config["provider"],
                "name": test_config["model"],
                "params": {
                    "temperature": test_config["temperature"]
                }
            },
            "prompts": {
                "system_prompt": OPTIMIZED_SYSTEM_PROMPT,
                "step_wise_prompt": OPTIMIZED_STEP_PROMPT
            }
        },
        "agent1": {
            "model": {
                "provider": "OpenRouter",
                "model": "deepseek/deepseek-chat-v3.1",
                "params": {
                    "temperature": 0.7
                }
            },
            "prompts": {
                "system_prompt": "You are a competitive chess player. Make smart, legal moves.",
                "step_wise_prompt": """Playing as {role}

Board: {board}
Legal moves: {valid_moves}
History: {past_up_to_five_moves}

Choose your best move from the legal moves list. Format: [move]"""
            }
        }
    }

    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return output_file


def run_test(test_config):
    """Run a single test game"""
    print(f"\n{'='*80}")
    print(f"🎮 Testing: {test_config['name']}")
    print(f"   Model: {test_config['model']}")
    print(f"   Provider: {test_config['provider']}")
    print(f"   Temperature: {test_config['temperature']}")
    print(f"{'='*80}\n")

    # Create config
    create_test_config(test_config)

    # Run game
    start_time = time.time()
    try:
        result = subprocess.run(
            ["uv", "run", "regular_chess.py"],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max per game
        )
        elapsed_time = time.time() - start_time

        # Parse results
        results_dir = Path("Results")
        if results_dir.exists():
            # Find the latest match
            matches = sorted(results_dir.glob("*/*"), key=os.path.getmtime, reverse=True)
            if matches:
                latest_match = matches[0]

                # Read game info
                game_info_file = latest_match / "game_info.json"
                log_file = latest_match / "log.txt"

                game_info = {}
                if game_info_file.exists():
                    with open(game_info_file) as f:
                        game_info = json.load(f)

                # Check for invalid moves
                invalid_moves = 0
                if log_file.exists():
                    with open(log_file) as f:
                        log_content = f.read()
                        invalid_moves = log_content.count("Random fallback")

                return {
                    "name": test_config["name"],
                    "model": test_config["model"],
                    "provider": test_config["provider"],
                    "success": True,
                    "time": elapsed_time,
                    "game_info": game_info,
                    "invalid_moves": invalid_moves,
                    "log_path": str(log_file)
                }

        return {
            "name": test_config["name"],
            "model": test_config["model"],
            "success": False,
            "error": "No results found",
            "time": elapsed_time
        }

    except subprocess.TimeoutExpired:
        return {
            "name": test_config["name"],
            "model": test_config["model"],
            "success": False,
            "error": "Timeout (>10 minutes)",
            "time": 600
        }
    except Exception as e:
        return {
            "name": test_config["name"],
            "model": test_config["model"],
            "success": False,
            "error": str(e),
            "time": time.time() - start_time
        }


def main():
    print("🏆 Comprehensive Chess Model Testing")
    print("=" * 80)
    print("\nTesting all approved models to find the best performer...")
    print(f"Total models to test: {len(TEST_CONFIGS)}")

    # Sort by priority
    sorted_configs = sorted(TEST_CONFIGS, key=lambda x: x["priority"])

    results = []

    for i, config in enumerate(sorted_configs, 1):
        print(f"\n📊 Test {i}/{len(sorted_configs)}")
        result = run_test(config)
        results.append(result)

        # Print summary
        if result["success"]:
            print(f"✅ Success!")
            print(f"   Time: {result['time']:.1f}s")
            print(f"   Invalid moves: {result['invalid_moves']}")
            if result.get("game_info"):
                print(f"   Game info: {result['game_info']}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")

        # Small delay between tests
        if i < len(sorted_configs):
            print("\n⏸️  Waiting 5 seconds before next test...")
            time.sleep(5)

    # Generate report
    print("\n\n" + "=" * 80)
    print("📊 FINAL RESULTS SUMMARY")
    print("=" * 80)

    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]

    if successful_tests:
        # Sort by performance (fewer invalid moves, faster time)
        successful_tests.sort(key=lambda x: (x["invalid_moves"], x["time"]))

        print("\n🏆 SUCCESSFUL TESTS (ranked by performance):\n")
        for i, result in enumerate(successful_tests, 1):
            print(f"{i}. {result['name']}")
            print(f"   Model: {result['model']}")
            print(f"   Invalid moves: {result['invalid_moves']}")
            print(f"   Time: {result['time']:.1f}s")
            print(f"   Log: {result.get('log_path', 'N/A')}")
            print()

        # Recommend best config
        best = successful_tests[0]
        print("\n" + "🎯" * 40)
        print(f"🏆 RECOMMENDED CONFIGURATION:")
        print(f"   Name: {best['name']}")
        print(f"   Model: {best['model']}")
        print(f"   Provider: {best['provider']}")
        print(f"   Invalid moves: {best['invalid_moves']}")
        print(f"   Time: {best['time']:.1f}s")
        print("🎯" * 40)

    if failed_tests:
        print("\n❌ FAILED TESTS:\n")
        for result in failed_tests:
            print(f"- {result['name']}: {result.get('error', 'Unknown')}")

    # Save results
    results_file = "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Detailed results saved to: {results_file}")


if __name__ == "__main__":
    main()

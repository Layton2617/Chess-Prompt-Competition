# 🏆 Chess Competition Optimization Guide

## 📋 Assignment Summary

- **Goal**: Submit best chess-playing agent via `config.yml`
- **Model Options**: 12 approved models (DeepSeek, GPT, Gemini, Claude, etc.)
- **Time Limit**: 3 minutes per move
- **Game Length**: 100 steps (50 moves per player)
- **Evaluation**: Stockfish-style winning probability
- **Submission**: `agent0` in config.yml

## 🎯 Optimization Strategy

### Phase 1: Model Selection

#### Recommended Models (in priority order):

1. **`deepseek/deepseek-r1-0528`** ⭐⭐⭐⭐⭐
   - Specialized reasoning model
   - Best for strategic thinking
   - Config: `config_optimized.yml`

2. **`gpt-4o-mini`** ⭐⭐⭐⭐
   - Proven good performance in tests
   - Stable and reliable
   - Config: `config_v2_gpt4o.yml`

3. **`deepseek/deepseek-chat-v3.1`** ⭐⭐⭐⭐
   - Strong performance
   - Fast response
   - Cost-effective

4. **`google/gemini-2.5-flash-preview-09-2025`** ⭐⭐⭐
   - Latest version
   - May have improvements
   - Worth testing

### Phase 2: Prompt Engineering

#### Key Components of Winning Prompts:

✅ **1. Provide Complete Information**
```yaml
- Board state with coordinates
- All piece positions
- Legal moves list
- Recent move history
```

✅ **2. Structured Reasoning**
```yaml
- Threat assessment
- Opportunity identification
- Strategy evaluation
- Move comparison
- Final decision
```

✅ **3. Output Format Control**
```yaml
- Clear UCI format requirement: [e2e4]
- Must use square brackets
- Must be from legal moves list
```

✅ **4. Chess Strategy Guidance**
```yaml
- Control center (e4, d4, e5, d5)
- Develop pieces early
- King safety / castling
- Tactical patterns (forks, pins, etc.)
```

✅ **5. Error Prevention**
```yaml
- Emphasize legal moves only
- Clarify piece notation (lowercase=black, UPPERCASE=white)
- Repeat format requirements
```

### Phase 3: Testing & Refinement

#### Test Process:

1. **Run each config version**
   ```bash
   chmod +x test_configs.sh
   ./test_configs.sh
   ```

2. **Analyze results**
   ```bash
   # Check Results/ folder
   - game_info.json: Who won?
   - log.txt: Move quality?
   - stepsinfo.json: Any random fallbacks?
   ```

3. **Compare metrics**
   - Win/loss/draw rate
   - Number of invalid moves
   - Average move time
   - Strategic quality (center control, development)

4. **Iterate**
   - Adjust temperature (0.5-0.8)
   - Refine prompt wording
   - Add specific tactical hints
   - Test edge cases

## 🔬 Testing Checklist

### Before Submission:

- [ ] Run at least 3 test games with your config
- [ ] Check for zero invalid moves (no random fallback)
- [ ] Verify moves complete within 3 minutes
- [ ] Review move quality in log.txt
- [ ] Test against different opponent strategies
- [ ] Confirm UCI format is correct: [a2a4]
- [ ] Validate agent0 is your submission agent

### Red Flags to Fix:

- ⚠️ "Random fallback move selected" in logs
- ⚠️ Moves taking >2 minutes
- ⚠️ Repetitive moves (not developing)
- ⚠️ King left in dangerous positions
- ⚠️ Not controlling center

## 📊 Configuration Versions

### Version 1: DeepSeek R1 (Recommended)
- **File**: `config_optimized.yml`
- **Model**: `deepseek/deepseek-r1-0528`
- **Strategy**: Structured reasoning with tactical checklist
- **Temperature**: 0.7 (balanced)
- **Best for**: Strategic thinking, long-term planning

### Version 2: GPT-4o-mini (Safe Choice)
- **File**: `config_v2_gpt4o.yml`
- **Model**: `gpt-4o-mini`
- **Strategy**: Grandmaster framework with position evaluation
- **Temperature**: 0.6 (focused)
- **Best for**: Consistent, reliable play

### Version 3: Aggressive Tactical
- **File**: `config_v3_aggressive.yml`
- **Model**: `deepseek/deepseek-r1-0528`
- **Strategy**: Tactical checklist (forks, pins, checks)
- **Temperature**: 0.5 (precise)
- **Best for**: Attacking play, creating threats

## 🚀 Quick Start

### Step 1: Test all versions
```bash
# Method A: Automated testing
chmod +x test_configs.sh
./test_configs.sh

# Method B: Manual testing
cp config_optimized.yml config.yml
uv run regular_chess.py
```

### Step 2: Analyze results
```bash
# Check the latest results
ls -lt Results/

# Review game logs
cat Results/[latest_match]/white_player_agent0/log.txt
```

### Step 3: Select winner
```bash
# Copy best config to config.yml
cp config_optimized.yml config.yml  # or v2 or v3
```

### Step 4: Final validation
```bash
# Run one final test game
uv run regular_chess.py

# Check for issues
grep -i "random fallback" Results/*/white_player_agent0/log.txt
```

### Step 5: Submit
```bash
# Submit config.yml via Canvas
# Make sure agent0 is your entry!
```

## 💡 Advanced Optimization Tips

### Temperature Tuning
- **0.3-0.5**: Very focused, deterministic (good for tactical positions)
- **0.6-0.7**: Balanced (recommended for general play)
- **0.8-1.0**: Creative, varied (good for complex positions)

### Prompt Refinement
1. **Add specific opening knowledge**: "In the opening, prioritize e4/d4/Nf3/Nc3"
2. **Endgame guidance**: "In endgame, activate king and push passed pawns"
3. **Piece value reminders**: "Q=9, R=5, B=3, N=3, P=1"
4. **Pattern recognition**: "Look for: back rank mate, knight forks, bishop pins"

### Model-Specific Tips

**For DeepSeek R1**:
- Leverage reasoning capability with step-by-step framework
- Use lower temperature (0.5-0.6)
- Provide structured analysis format

**For GPT-4o-mini**:
- Clear, concise instructions work best
- Can handle more creative temperature (0.7-0.8)
- Good at following format requirements

## 📈 Expected Performance

### Good Performance Indicators:
- ✅ 0 invalid moves (no random fallback)
- ✅ Center control by move 10
- ✅ All pieces developed by move 15
- ✅ King castled by move 12
- ✅ Average move time < 30 seconds
- ✅ Winning or drawing against test opponents

### Warning Signs:
- ❌ Multiple random fallbacks
- ❌ King left in center past move 10
- ❌ Pieces not developed
- ❌ Repetitive moves
- ❌ Losing material without compensation

## 🎓 Learning from Test Games

### What to Look For in Logs:

1. **Opening phase (moves 1-10)**
   - Did agent control center?
   - Were pieces developed efficiently?
   - Any wasted moves?

2. **Middle game (moves 11-30)**
   - Were threats created/handled?
   - Piece coordination?
   - Tactical opportunities seized?

3. **Endgame (moves 31+)**
   - King activated?
   - Passed pawns created/stopped?
   - Proper technique?

## 🏁 Final Checklist

Before submitting `config.yml`:

- [ ] Model is from approved list
- [ ] `agent0` is configured (this is your submission!)
- [ ] Temperature is appropriate (0.5-0.8)
- [ ] System prompt provides strategic guidance
- [ ] Step_wise_prompt includes:
  - [ ] Board visualization
  - [ ] Piece positions
  - [ ] Legal moves list
  - [ ] Move history
  - [ ] Structured reasoning framework
  - [ ] Clear output format requirement
- [ ] Tested at least 3 games
- [ ] No invalid move warnings in logs
- [ ] Move times within limits
- [ ] Ready to submit via Canvas!

## 🤝 Support

- Test your configs: `uv run regular_chess.py`
- Check results: `Results/[match_id]/white_player_agent0/`
- Debug issues: Look for "Random fallback" or errors in log.txt

Good luck in the competition! 🏆♟️

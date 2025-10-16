# Chess Prompt Competition

An optimized chess game arena for testing and comparing LLM performance with different prompts in chess. Built upon the TextArena framework (https://github.com/LeonGuertler/TextArena), this project enables two AI agents to play chess against each other using configurable prompts and different LLM providers.

## Features

- **Multi-Provider Support**: OpenAI, OpenRouter, and Google Gemini
- **Fully Configurable Prompts**: Customize system and step-wise prompts for each agent
- **Optimized Configurations**: Pre-tuned configurations for better performance
- **Comprehensive Testing**: Built-in test scripts for performance evaluation

## Quick Start

### Setup Environment
```bash
uv sync
```

### Configure API Keys
Add your API keys in a `.env` file:
```bash
# Copy .env.example to .env
cp .env.example .env

# Then edit .env and add your API keys:
OPENAI_API_KEY=your-openai-key
OPENROUTER_API_KEY=your-openrouter-key
GEMINI_API_KEY=your-gemini-key
```

### Run with Default Prompts
```bash
uv run regular_chess.py
```

## Configuration

The project uses `config.yml` for configuration and `.env` for API keys:

- **API Keys**: Set in `.env` file (OPENAI_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY)
- **Agent Configuration**: Each agent is configured separately with its model and prompts in `config.yml`:
  ```yaml
  agent0:
    model:
      provider: "OpenAI"  # OpenAI, OpenRouter, or Gemini
      name: "gpt-4o-mini"
      params:  # Any parameters supported by the agent
        temperature: 1.0
        max_tokens: 1000
    prompts:
      system_prompt: |
        Your system prompt here
      step_wise_prompt: |
        Your step-wise prompt template here
  
  agent1:
    model:
      provider: "OpenRouter"
      name: "google/gemini-2.5-flash"
      params:
        temperature: 1.0
    prompts:
      system_prompt: |
        Your system prompt here
      step_wise_prompt: |
        Your step-wise prompt template here
  ```
  The `params` section supports any parameters accepted by the respective agent APIs:
  - **OpenAI/OpenRouter**: Passed as `**kwargs` to the API (temperature, max_tokens, top_p, frequency_penalty, presence_penalty, etc.)
  - **Gemini**: Passed as `generation_config` dict (temperature, top_p, top_k, max_output_tokens, etc.)
- **Game Settings**:
  - `num_players`: Number of players (2 for chess)
  - `stop_after`: Maximum number of moves per game
- **Prompts**: Fully customizable prompts for both agents

## Prompt Engineering

Each agent has two configurable prompts in `config.yml`:

1. **system_prompt**: The system prompt that defines the agent's behavior and personality
2. **step_wise_prompt**: The template used for each move's LLM call

Both agents can have different prompts, allowing you to test different strategies against each other.

Note: The retry prompt (used when an invalid move is attempted) is hard-coded in the application.

### Step-wise Prompt Parameters

The `step_wise_prompt` template for each agent supports the following variables:
- `role`: Player color (White or Black)
- `board`: String representation of the current board state with coordinates (ASCII art)
- `piece_positions`: List of all pieces and their positions (e.g., "White pieces: K-e1, Q-d1, R-a1, R-h1, ...\nBlack pieces: k-e8, q-d8, r-a8, r-h8, ...")
- `valid_moves`: Set of valid moves in UCI format
- `full_observation`: Complete observation including board, move, and valid moves for each step
- `past_up_to_five_moves`: Formatted string of the last up to 5 moves with player labels (e.g., "White: [e2e4]\nBlack: [e7e5]")

## Game Results

Results are saved in the `Results/` directory with game logs and move history. Please check the logs to optimize your prompts.

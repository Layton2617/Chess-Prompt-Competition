"""
Chess game runner, implements a random fall back mechanism for the action.
"""

import time
import uuid
import random
import os
from os.path import join
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv

import textarena as ta
from utils import Utils
import yaml


class Config:
    """Configuration management with YAML support"""
    
    def __init__(self, config_path: Optional[str] = "./config.yml"):
        if config_path and config_path.endswith('.yml'):
            self._load_from_yaml(config_path)
    
    def _load_from_yaml(self, config_path: str):
        """Load configuration from YAML file"""
        try:
            # Load environment variables from .env file
            load_dotenv(dotenv_path='.env')
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            
            # API Configuration - load from environment variables only
            self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
            self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY', '')
            self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')

            # Agent 0 Configuration
            self.agent0_provider = config['agent0']['model']['provider']
            self.agent0_model_name = config['agent0']['model']['name']
            self.agent0_params = config['agent0']['model'].get('params', {})
            self.agent0_system_prompt = config['agent0']['prompts']['system_prompt']
            self.agent0_step_wise_prompt = config['agent0']['prompts']['step_wise_prompt']

            # Agent 1 Configuration
            self.agent1_provider = config['agent1']['model']['provider']
            self.agent1_model_name = config['agent1']['model']['name']
            self.agent1_params = config['agent1']['model'].get('params', {})
            self.agent1_system_prompt = config['agent1']['prompts']['system_prompt']
            self.agent1_step_wise_prompt = config['agent1']['prompts']['step_wise_prompt']

            # Game Configuration
            self.num_chess_players = config['game']['num_players']
            self.stop_after = config['game']['stop_after']
            
        except Exception as e:
            print(f"Error loading YAML config: {e}")




class GameLogger:
    
    def __init__(self, base_path: str, run_id: str):
        self.base_path = base_path
        self.run_id = run_id
        self.log_path = join(base_path, str(run_id), "log.txt")
    
    def log(self, level: str, *args, save_log: bool = True) -> None:
        """Log message with specified level"""
        message = f"{level.upper()} {' '.join(str(arg) for arg in args)}\n"
        print(message, end='')
        
        if save_log:
            Utils.append_file(message, self.log_path)


class AgentManager:
    
    def __init__(self, openrouter_api_key: str, openai_api_key: str, gemini_api_key: str, white_player_name: str, black_player_name: str, white_player_prompt: str, black_player_prompt: str, white_player_provider: str, black_player_provider: str, white_player_params: Dict[str, Any] = None, black_player_params: Dict[str, Any] = None):
        self.openrouter_api_key = openrouter_api_key
        self.openai_api_key = openai_api_key
        self.gemini_api_key = gemini_api_key
        self.white_player_provider = white_player_provider
        self.black_player_provider = black_player_provider
        self.white_player_name = white_player_name
        self.black_player_name = black_player_name
        self.white_player_prompt = white_player_prompt
        self.black_player_prompt = black_player_prompt
        self.white_player_params = white_player_params or {}
        self.black_player_params = black_player_params or {}
    
    def create_agents(self) -> Dict[int, Any]:
        agents = {}

        agent_configs = [
            {
                "provider": self.white_player_provider,
                "name": self.white_player_name,
                "prompt": self.white_player_prompt,
                "params": self.white_player_params
            },
            {
                "provider": self.black_player_provider,
                "name": self.black_player_name,
                "prompt": self.black_player_prompt,
                "params": self.black_player_params
            }
        ]

        for i in range(2):
            if agent_configs[i]["provider"] == "OpenAI":
                # OpenAI accepts **kwargs that are passed to the API
                agents[i] = ta.agents.OpenAIAgent(
                    model_name=agent_configs[i]["name"],
                    system_prompt=agent_configs[i]["prompt"],
                    api_key=self.openai_api_key,
                    base_url="https://api.openai.com/v1",
                    verbose=False,
                    **agent_configs[i]["params"]
                )
            elif agent_configs[i]["provider"] == "OpenRouter":
                # OpenRouter accepts **kwargs that are passed to the API
                agents[i] = ta.agents.OpenRouterAgent(
                    model_name=agent_configs[i]["name"],
                    system_prompt=agent_configs[i]["prompt"],
                    api_key=self.openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    verbose=False,
                    **agent_configs[i]["params"]
                )
            elif agent_configs[i]["provider"] == "Gemini":
                # Gemini accepts generation_config as a dict parameter (not **kwargs)
                agents[i] = ta.agents.GeminiAgent(
                    model_name=agent_configs[i]["name"],
                    system_prompt=agent_configs[i]["prompt"],
                    api_key=self.gemini_api_key,
                    verbose=False,
                    generation_config=agent_configs[i]["params"] if agent_configs[i]["params"] else None
                )
            else:
                raise ValueError(f"Unknown provider: {agent_configs[i]['provider']}")

        return agents


class RegularChessRunner:
    """
    Main class for running regular chess games.
    
    This runner implements a random fall back mechanism for the action.
    """
    
    # Hard-coded retry prompt
    RETRY_PROMPT = (
        "Attempt {attempt} failed, please remember that you are acting as {role} in "
        "the chess game, and you need to make a valid move from the last valid moves list. "
        "Return the move in the format [UCI_MOVE], for example [e2e4]."
    )
    
    def __init__(
        self,
        white_player_name: str = "google/gemini-2.5-flash",
        black_player_name: str = "google/gemini-2.5-flash",
        white_player_prompt: str = "",
        black_player_prompt: str = "",
        white_player_step_wise_prompt: str = "",
        black_player_step_wise_prompt: str = "",
        white_player_provider: str = "OpenRouter",
        black_player_provider: str = "OpenRouter",
        white_player_params: Optional[Dict[str, Any]] = None,
        black_player_params: Optional[Dict[str, Any]] = None,
        max_turns: int = 100,
        config_path: Optional[str] = "./config.yml",
        results_dir: Optional[str] = None
    ):
        """Initialize the chess runner with configuration"""
        self.config = Config(config_path)

        self.white_player_name = white_player_name
        self.black_player_name = black_player_name
        self.white_player_prompt = white_player_prompt
        self.black_player_prompt = black_player_prompt
        self.white_player_step_wise_prompt = white_player_step_wise_prompt
        self.black_player_step_wise_prompt = black_player_step_wise_prompt
        self.white_player_provider = white_player_provider
        self.black_player_provider = black_player_provider
        self.white_player_params = white_player_params or {}
        self.black_player_params = black_player_params or {}
        self.max_turns = max_turns
        self.results_dir = results_dir
        self.logger: Optional[GameLogger] = None

        self.agent_manager = AgentManager(
            self.config.openrouter_api_key,
            self.config.openai_api_key,
            self.config.gemini_api_key,
            white_player_name,
            black_player_name,
            white_player_prompt,
            black_player_prompt,
            white_player_provider,
            black_player_provider,
            white_player_params,
            black_player_params
        )
        
        # Initialize environment
        self.env = self._create_environment()
        print("Chess environment initialized successfully")
    
    def _create_environment(self) -> ta.Env:
        env = ta.make(
            env_id="Chess-v0",
            is_open=True,
            max_turns=self.max_turns,
            show_valid=True
        )
        return env
    
    def _get_valid_moves(self) -> List[str]:
        """Get list of valid moves in UCI format"""
        return [f'[{move.uci()}]' for move in self.env.state.game_state["board"].legal_moves]
    
    def _agent_call_with_retry(
        self, 
        agent: Any, 
        observation: str, 
        player_id: int, 
        valid_moves: List[str],
        retries: int = 1
    ) -> Tuple[Optional[str], int, int, int, Dict]:
        """
        Call agent with retry logic and track only the final attempt.
        
        Returns:
            cleaned_action: The final move selected
            input_tokens: Input tokens from final attempt
            output_tokens: Output tokens from final attempt
            total_tokens: Total tokens from final attempt
            attempt_info: Dict with info about the final attempt
        """
        role = "White" if player_id == 0 else "Black"
        last_raw_action = None
        last_input_tokens = 0
        last_output_tokens = 0
        last_total_tokens = 0
        
        for attempt in range(retries):
            raw_action, input_tokens, output_tokens, total_tokens = agent(observation)
            cleaned_action = Utils.clean_chess_action(raw_action)
            
            # Keep track of last attempt
            last_raw_action = raw_action
            last_input_tokens = input_tokens
            last_output_tokens = output_tokens
            last_total_tokens = total_tokens
            
            if cleaned_action and cleaned_action in valid_moves:
                # Success - return info about this successful attempt
                attempt_info = {
                    "prompt_input": observation,
                    "llm_raw_output": raw_action,
                    "cleaned_action": cleaned_action,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "is_random_fallback": False
                }
                return cleaned_action, input_tokens, output_tokens, total_tokens, attempt_info
            
            # observation += self.RETRY_PROMPT.format(
            #     attempt=attempt + 1, 
            #     role=role
            # ) # disable the attempt prompt for simplicity
        
        # If we get here, all retries failed - use random fallback
        random_move = random.choice(valid_moves)

        # Return info about the failed attempt with random fallback
        attempt_info = {
            "prompt_input": observation,
            "llm_raw_output": last_raw_action,
            "cleaned_action": random_move,
            "input_tokens": last_input_tokens,
            "output_tokens": last_output_tokens,
            "total_tokens": last_total_tokens,
            "is_random_fallback": True,
            "failure_reason": f"All {retries} attempts failed. The action '{cleaned_action}' was not a valid move in the valid moves list {valid_moves}."
        }
        
        return random_move, 0, 0, 0, attempt_info
    
    def _current_agent_task(self, agent: Any, observation: str, player_id: int) -> Tuple[Optional[str], float, int, int, int, Dict]:
        """
        Execute the current agent's move selection.
        
        Returns:
            move: The selected move
            time_taken: Time taken for the move selection
            input_tokens: Input tokens from final attempt
            output_tokens: Output tokens from final attempt
            total_tokens: Total tokens from final attempt
            attempt_info: Dict with info about the final attempt
        """
        start_time = time.perf_counter()
        valid_moves = self._get_valid_moves()

        role = "White" if player_id == 0 else "Black"
        board_with_coords = Utils.board_with_coords(self.env.state.game_state['board'])
        piece_positions = Utils.list_piece_positions(self.env.state.game_state['board'])

        # Use the appropriate step_wise_prompt based on player_id (0=White, 1=Black)
        prompt_template = self.white_player_step_wise_prompt if player_id == 0 else self.black_player_step_wise_prompt
        truncated_observation, truncated_moves_list = Utils.truncate_observation(observation, 5)

        passed_observation = prompt_template.format(
            role=role,
            board=board_with_coords,
            piece_positions=piece_positions,
            valid_moves=valid_moves,
            full_observation=observation,
            past_up_to_five_moves=truncated_moves_list
        )

        move, input_tokens, output_tokens, total_tokens, attempt_info = self._agent_call_with_retry(agent, passed_observation, player_id, valid_moves)
        end_time = time.perf_counter()
        
        return move, end_time - start_time, input_tokens, output_tokens, total_tokens, attempt_info
    
    def _execute_game_loop(
        self,
        agents: Dict[int, Any],
        stop_after: Optional[int] = None
    ) -> Tuple[Dict[int, Any], Any, Any, float, float]:
        """Main game execution loop"""
        self.env.reset(num_players=self.config.num_chess_players)
        
        steps_info = {}
        step_count = 0
        done = False

        current_agent = agents[0]
        other_agent = agents[1]
        
        regular_time = 0.0


        # Initialize game state
        player_id, observation = self.env.get_observation()
        
        while not done:

            player_id, observation = self.env.get_observation()


            current_future = self._current_agent_task(current_agent, observation, player_id)
                    
            current_move, time_taken1, input_tokens1, output_tokens1, total_tokens1, attempt_info = current_future
                
            # Update timing counters
            regular_time += time_taken1
            
            # Capture board state BEFORE move for steps_info (what the agent saw)
            board_before_move = "\n" + Utils.board_with_coords(self.env.state.game_state['board']) + '\n'
            
            # Enhanced logging for log.txt (before move execution)
            if self.logger:
                role = "White" if player_id == 0 else "Black"
                self.logger.log("INFO", f"{'='*100}")
                self.logger.log("INFO", f"STEP {step_count} | Player: {role} (ID: {player_id})")
                self.logger.log("INFO", f"{'='*100}")
                
                # Log board state BEFORE move
                self.logger.log("INFO", f"\nBOARD STATE BEFORE MOVE:")
                self.logger.log("INFO", Utils.board_with_coords(self.env.state.game_state['board']))
                
                # Log the final attempt
                self.logger.log("INFO", f"\nPROMPT INPUT:\n{attempt_info['prompt_input']}")
                self.logger.log("INFO", f"\nLLM RAW OUTPUT:\n{attempt_info['llm_raw_output']}")
                self.logger.log("INFO", f"\nCLEANED ACTION: {attempt_info['cleaned_action']}")
                
                # Add failure note if it was a random fallback
                if attempt_info.get('is_random_fallback'):
                    self.logger.log("INFO", f"\n⚠️  NOTE: {attempt_info['failure_reason']}")
                    self.logger.log("INFO", f"Random fallback move selected: {attempt_info['cleaned_action']}")
                
                self.logger.log("INFO", f"\nTOKENS - Input: {attempt_info['input_tokens']}, Output: {attempt_info['output_tokens']}, Total: {attempt_info['total_tokens']}")
                self.logger.log("INFO", f"\nFINAL MOVE: {current_move}")
                self.logger.log("INFO", f"TIME TAKEN: {time_taken1:.3f}s")
            
            # Execute move
            done, info = self.env.step(current_move)
            
            # Record step information (including full prompt and output)
            # Note: current_observation is the board BEFORE the move (what the agent saw)
            steps_info[step_count] = {
                "player_id": player_id,
                "current_observation": board_before_move,
                "current_move": current_move,
                "time_taken_current_agent": time_taken1,
                "input_tokens_current_agent": input_tokens1,
                "output_tokens_current_agent": output_tokens1,
                "total_tokens_current_agent": total_tokens1,
                "attempt_info": attempt_info  # Info about the final attempt
            }
            
            # Log board state AFTER move execution
            if self.logger:
                self.logger.log("INFO", f"\nBOARD STATE AFTER MOVE:")
                self.logger.log("INFO", Utils.board_with_coords(self.env.state.game_state['board']))
                self.logger.log('-' * 100)
            step_count += 1
            
            if stop_after and step_count >= stop_after:
                break
            
            # Swap agents for next turn
            current_agent, other_agent = other_agent, current_agent
        
        rewards, game_info = self.env.close()
        return steps_info, rewards, game_info, regular_time
    
    def run(self, stop_after: int = 100, match_id: str = None, game_label: str = None) -> None:
        """Run a complete chess game"""
        # Setup run
        if match_id is None:
            match_id = str(uuid.uuid4())

        if game_label is None:
            game_label = str(uuid.uuid4())
        
        match_info = f"{self.white_player_name} vs {self.black_player_name}"
        match_dir = join(self.results_dir, match_info, match_id)
        self.logger = GameLogger(match_dir, game_label)

        current_dir_path = join(match_dir, game_label)
        
        # Create agents
        agents = self.agent_manager.create_agents()
        
        self.logger.log("INFO", f"Starting run with White Player: {self.white_player_name} with prompt \n{self.white_player_prompt} \nBlack Player: {self.black_player_name} with prompt \n{self.black_player_prompt}")
        
        try:
            # Execute game
            steps_info, rewards, game_info, regular_time = self._execute_game_loop(
                agents, stop_after
            )
            
            # Save results
            Utils.save_json(steps_info, join(current_dir_path, "stepsinfo.json"))
            Utils.save_json(rewards, join(current_dir_path, "rewards.json"))
            Utils.save_json(game_info, join(current_dir_path, "game_info.json"))
            
            self.logger.log("INFO", f"Run completed for match {match_id} and game {game_label}")
            
        except Exception as e:
            if self.logger:
                self.logger.log("ERROR", str(e))
            raise


def main():
    """Main execution function"""
    config_path = "./config.yml"
    config = Config(config_path)

    # Generate a unique match ID for this pair of games
    match_id = str(uuid.uuid4())

    # Create a directory for the results
    results_dir = f"./Results"
    os.makedirs(results_dir, exist_ok=True)

    # Agent Configuration
    agent0_name = config.agent0_model_name
    agent0_provider = config.agent0_provider
    agent0_params = config.agent0_params
    agent0_system_prompt = config.agent0_system_prompt
    agent0_step_wise_prompt = config.agent0_step_wise_prompt
    
    agent1_name = config.agent1_model_name
    agent1_provider = config.agent1_provider
    agent1_params = config.agent1_params
    agent1_system_prompt = config.agent1_system_prompt
    agent1_step_wise_prompt = config.agent1_step_wise_prompt

    print(f"Starting match {match_id}: {agent0_name} vs {agent1_name}")

    # Game: Agent0 as White, Agent1 as Black
    runner_agent0_as_white = RegularChessRunner(
        white_player_name=agent0_name,
        white_player_provider=agent0_provider,
        white_player_params=agent0_params,
        white_player_prompt=agent0_system_prompt,
        white_player_step_wise_prompt=agent0_step_wise_prompt,
        black_player_name=agent1_name,
        black_player_provider=agent1_provider,
        black_player_params=agent1_params,
        black_player_prompt=agent1_system_prompt,
        black_player_step_wise_prompt=agent1_step_wise_prompt,
        max_turns=config.stop_after,
        results_dir=results_dir
    )

    start_time = time.time()
    print("Game: Agent0 as White, Agent1 as Black")
    runner_agent0_as_white.run(stop_after=config.stop_after, match_id=match_id, game_label="white_player_agent0")
    game_time = time.time() - start_time

    print(f"Match {match_id} completed!")
    print(f"Game time: {game_time:.2f} seconds")
    print(f"Results saved in: ./Results/{match_id}/")


if __name__ == "__main__":
    main()
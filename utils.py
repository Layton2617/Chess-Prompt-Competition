import os
import json
import shutil
import re
import chess
from typing import Optional
from pathlib import Path

class Utils:

    @staticmethod
    def read_json(path):
        with open(path, "r") as f:
            return json.load(f)
    
    @staticmethod
    def save_json(obj, path, delete_prev_file=False):
        if os.path.exists(path) and delete_prev_file:
            os.remove(path)
        with open(path, "w") as f:
            json.dump(obj, f, indent=4)
    
    @staticmethod
    def read_file(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    @staticmethod
    def save_file(string, path, delete_prev_file=False):
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)

        if os.path.exists(path) and delete_prev_file:
            os.remove(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(string)

    @staticmethod
    def join_prompt(*args):
        """Join prompt parts. Consider using ''.join(args) directly for simple cases."""
        return "".join(args)

    @staticmethod
    def append_file(string, path):
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(string+"\n")
    
    @staticmethod
    def dict_to_str(d):
        return ' | '.join([f"{k}: {v}" for k, v in d.items()])

    @staticmethod
    def board_with_coords(board: chess.Board) -> str:
        inner_width = len(str(board).splitlines()[0])
        top = bottom = f"   +{'-' * (inner_width + 2)}+"
        body = [f" {rank} | {row} |" for rank, row in zip(range(8, 0, -1), str(board).splitlines())]
        files = "   " + " ".join("a b c d e f g h".split()).center(inner_width + 2)
        return "\n".join([top, *body, bottom, files])

    @staticmethod
    def list_piece_positions(board: chess.Board) -> str:
        """
        Generate a formatted list of all pieces and their positions on the board.
        
        Returns:
            A string with piece positions grouped by color, e.g.:
            "White pieces: K-e1, Q-d1, R-a1, R-h1, ...
             Black pieces: k-e8, q-d8, r-a8, r-h8, ..."
        """
        white_pieces = []
        black_pieces = []
        
        # Iterate through all squares
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                square_name = chess.square_name(square)
                piece_symbol = piece.symbol()
                
                if piece.color == chess.WHITE:
                    white_pieces.append(f"{piece_symbol}-{square_name}")
                else:
                    black_pieces.append(f"{piece_symbol}-{square_name}")
        
        # Sort pieces by type (K, Q, R, B, N, P for white; k, q, r, b, n, p for black)
        piece_order = {'K': 0, 'Q': 1, 'R': 2, 'B': 3, 'N': 4, 'P': 5, 
                       'k': 0, 'q': 1, 'r': 2, 'b': 3, 'n': 4, 'p': 5}
        white_pieces.sort(key=lambda x: piece_order.get(x[0], 6))
        black_pieces.sort(key=lambda x: piece_order.get(x[0], 6))
        
        white_str = "White pieces: " + ", ".join(white_pieces) if white_pieces else "White pieces: none"
        black_str = "Black pieces: " + ", ".join(black_pieces) if black_pieces else "Black pieces: none"
        
        return f"{white_str}\n{black_str}"

    @staticmethod
    def clean_chess_action(action: Optional[str]) -> Optional[str]:
        """
        Return the last valid chess action from the action string.
        """
        UCI_PATTERN = re.compile(r'\[?\s*([a-h][1-8][a-h][1-8][qrbn]?)\s*\]?')
        if action is None:
            return None
        
        # Find all matches and take the last one
        matches = UCI_PATTERN.findall(action)
        if matches:
            return f'[{matches[-1]}]'
        
        return None

    @staticmethod
    def truncate_observation(observation: str, truncate_steps: int):
        """
        Truncates the observation to the last truncate_steps moves and extracts actions.
        If there are fewer moves than truncate_steps, returns all available moves.
        
        Args:
            observation: The full game observation string
            truncate_steps: Maximum number of moves to keep
        
        Returns:
            tuple: (truncated_observation, formatted_moves_string)
                - truncated_observation: String with up to the last truncate_steps moves
                - formatted_moves_string: Formatted string with player labels (e.g., "White: [e2e4]\nBlack: [e7e5]")
        """
        lines = observation.split('\n')
        
        # Find all move lines (lines that contain "made the following move:")
        move_indices = []
        actions = []
        
        for i, line in enumerate(lines):
            if "made the following move:" in line:
                move_indices.append(i)
                # Extract the move (last word in the line)
                move = line.strip().split()[-1]
                actions.append(move)
        
        # Determine how many moves to keep (min of truncate_steps and actual moves)
        num_moves_to_keep = min(truncate_steps, len(move_indices))
        
        if num_moves_to_keep == 0:
            # No moves yet, return the full observation
            return observation, "[]"
        
        # Find the starting index for truncation
        start_move_idx = move_indices[-num_moves_to_keep]
        
        # Keep the game header and everything from the start_move_idx onwards
        truncated_lines = lines[:1] + lines[start_move_idx:]
        actions = actions[-num_moves_to_keep:]
        
        truncated_observation = '\n'.join(truncated_lines)
        
        # Format moves with player labels
        # Need to figure out which player made the first move in our truncated list
        # Total moves made = len(all actions), last num_moves_to_keep = actions list
        total_moves_made = len([l for l in lines if "made the following move:" in l])
        first_move_index = total_moves_made - num_moves_to_keep
        
        formatted_moves = []
        for idx, move in enumerate(actions):
            # White moves on even indices (0, 2, 4...), Black on odd (1, 3, 5...)
            move_number = first_move_index + idx
            player = "White" if move_number % 2 == 0 else "Black"
            formatted_moves.append(f"{player}: {move}")
        
        formatted_moves_string = "\n".join(formatted_moves)
        
        return truncated_observation, formatted_moves_string
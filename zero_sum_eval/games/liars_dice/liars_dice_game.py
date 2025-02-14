import random
from typing import Dict, List
from zero_sum_eval.game_state import Action, GameState, InvalidMoveError, PlayerDefinition
from zero_sum_eval.registry import GAME_REGISTRY
from zero_sum_eval.player import Move
from .liars_dice_player import LiarsDicePlayer, PLAYER_0_KEY, PLAYER_1_KEY

@GAME_REGISTRY.register("liars_dice")
class LiarsDiceGame(GameState):
    """
    Implementation of Liar's Dice game where players take turns bidding on dice
    or calling the previous player's bluff.
    """
    
    def __init__(self, num_dice: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.num_dice = num_dice
        self.reset_game()

    def reset_game(self):
        """Reset the game state for a new game"""
        self.dice = {
            PLAYER_0_KEY: sorted([random.randint(1,6) for _ in range(self.num_dice)]),
            PLAYER_1_KEY: sorted([random.randint(1,6) for _ in range(self.num_dice)])
        }
        self.current_bid = (0, 0)  # (quantity, face_value)
        self.history = []
        self.scores = {PLAYER_0_KEY: 0, PLAYER_1_KEY: 0}
        self.message = f"{PLAYER_0_KEY} to bid"

    def update_game(self, move: Move):
        """Process a player's move"""
        action = move.value.strip()
        
        if action == "[Call]":
            # Count total dice matching the current bid
            total = sum(
                dice.count(self.current_bid[1])
                for dice in self.dice.values()
            )
            
            # Determine winner
            caller = self.get_next_action().player.player_key
            bidder = PLAYER_1_KEY if caller == PLAYER_0_KEY else PLAYER_0_KEY
            
            if total < self.current_bid[0]:
                self.scores = {caller: 1, bidder: 0}
            else:
                self.scores = {caller: 0, bidder: 1}
                
            self.message = f"Game Over - {total} {self.current_bid[1]}s found"
            
        elif action.startswith("[Bid] "):
            try:
                _, quantity, face = action.split()
                quantity = int(quantity)
                face = int(face)
                
                # Validate bid
                if face < 1 or face > 6:
                    raise InvalidMoveError("Face value must be between 1 and 6")
                    
                if quantity < 1:
                    raise InvalidMoveError("Quantity must be positive")
                    
                if quantity <= self.current_bid[0] and face <= self.current_bid[1]:
                    raise InvalidMoveError("New bid must increase quantity or face value")
                    
                self.current_bid = (quantity, face)
                self.message = f"Current bid: {quantity} {face}s"
                
            except ValueError:
                raise InvalidMoveError("Invalid bid format")
                
        else:
            raise InvalidMoveError("Invalid action format")
            
        self.history.append(action)

    def is_over(self) -> bool:
        """Check if the game is over"""
        return self.history and self.history[-1] == "[Call]"

    def get_scores(self):
        """Get the current scores"""
        return self.scores

    def get_next_action(self) -> Action:
        """Get the next player's action"""
        return Action(
            "MakeBid",
            self.players[PLAYER_0_KEY if len(self.history) % 2 == 0 else PLAYER_1_KEY]
        )

    def player_inputs(self) -> Dict[str, str]:
        """Get the inputs for the next player's turn"""
        player_key = self.get_next_action().player.player_key
        return {
            'dice_roll': str(self.dice[player_key]),
            'current_bid': f"{self.current_bid[0]} {self.current_bid[1]}" if self.current_bid[0] > 0 else "0 0",
            'history': "\n".join(self.history)
        }

    def player_definitions(self) -> List[PlayerDefinition]:
        """Define the players for this game"""
        return [
            PlayerDefinition(player_key=PLAYER_0_KEY, actions=["MakeBid"], default_player_class=LiarsDicePlayer),
            PlayerDefinition(player_key=PLAYER_1_KEY, actions=["MakeBid"], default_player_class=LiarsDicePlayer)
        ]

    def display(self) -> str:
        """Create a string representation of the game state"""
        display_str = f"Message: {self.message}\n"
        display_str += f"Current bid: {self.current_bid[0]} {self.current_bid[1]}s\n"
        display_str += f"Player 0 dice: {self.dice[PLAYER_0_KEY]}\n"
        display_str += f"Player 1 dice: {self.dice[PLAYER_1_KEY]}\n"
        display_str += f"History:\n" + "\n".join(self.history) + "\n"
        if self.is_over():
            display_str += f"Scores: {self.scores}\n"
        return display_str

    def export(self):
        """Export the game state"""
        return {
            'message': self.message,
            'current_bid': f"{self.current_bid[0]} {self.current_bid[1]}",
            'history': self.history,
            'scores': self.scores,
            **(getattr(self, '_log', {}))  # Safely include _log if it exists
        }

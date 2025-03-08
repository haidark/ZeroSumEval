from typing import Dict
import dspy
from zero_sum_eval.core.player import Player
from zero_sum_eval.core.registry import PLAYER_REGISTRY

class MakeMoveSignature(dspy.Signature):
    """You are an expert poker player and you need to make a move in a poker game."""
    hole_cards = dspy.InputField(desc="Your hole cards")
    community_cards = dspy.InputField(desc="The community cards on the table")
    pot = dspy.InputField(desc="Current pot size")
    current_bet = dspy.InputField(desc="Current bet amount")
    chips = dspy.InputField(desc="Your remaining chips")
    stage = dspy.InputField(desc="Current stage of the game (preflop, flop, turn, river)")
    history = dspy.InputField(desc="History of moves in the current hand")
    
    action: str = dspy.OutputField(desc='The chosen poker move: either "Fold", "Call", or "Raise"')
    amount: int = dspy.OutputField(desc='The amount to raise, if the action is "Raise"')

class PokerMoveModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.make_move = dspy.ChainOfThought(MakeMoveSignature)

    def forward(
        self,
        hole_cards: str,
        community_cards: str,
        pot: int,
        current_bet: int,
        chips: int,
        stage: str,
        history: str,
    ) -> dspy.Prediction:
        """Generate a poker move based on the current game state"""
        move = self.make_move(
            hole_cards=hole_cards,
            community_cards=community_cards,
            pot=pot,
            current_bet=current_bet,
            chips=chips,
            stage=stage,
            history=history,
        )

        action = move.action
        amount = move.amount

        # Validate the action
        dspy.Suggest(action in ["Fold", "Call", "Raise"], "The action must be one of the following: Fold, Call, Raise")

        # Validate the amount to raise
        if action == "Raise":
            try:
                amount = int(amount)
            except ValueError:
                dspy.Suggest(False, "The amount to raise must be a number")
            
            dspy.Suggest(amount > 0, "The amount to raise must be greater than 0")
            dspy.Suggest(amount <= chips, "The amount to raise must be less than or equal to the player's remaining chips")


        output = f"{action} {amount}"

        return dspy.Prediction(rationale=move.rationale, output=output)


@PLAYER_REGISTRY.register("poker", "poker_player")
class PokerPlayer(Player):    
    def init_actions(self) -> Dict[str, dspy.Module]:
        """Initialize the action modules for the player"""
        return {
            "MakeMove": PokerMoveModule()
        }

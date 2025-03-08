import dspy
from zero_sum_eval.core.player import Player
from zero_sum_eval.core.registry import PLAYER_REGISTRY, METRIC_REGISTRY

# Player keys
PLAYER_0_KEY = "player_0"
PLAYER_1_KEY = "player_1"

class MakeBidSignature(dspy.Signature):
    """You are playing Liar's Dice. Each player has 5 dice hidden from other players.
    Players take turns making bids about how many dice of a certain value exist among ALL dice in play.
    A bid consists of a quantity and a face value (e.g. "three 4s" means "there are at least three 4s total").
    
    On your turn you must either:
    1. Make a higher bid than the previous bid by:
       - Increasing the quantity for any face value
       - OR keeping the same quantity but bidding a higher face value
    2. Call "liar" if you think the previous bid is too high
    
    Example valid bids:
    - If current bid is "two 3s", you can bid "three 2s", "three 3s", "two 4s", etc.
    - If no previous bid, you can make any bid like "[Bid] 1 3" for "one 3"
    - To call liar on previous bid, respond with exactly "[Call]"
    """
    dice_roll = dspy.InputField(desc="Your current dice roll (these are your hidden dice)")
    current_bid = dspy.InputField(desc="Current bid in format: quantity face_value (e.g. '3 4' means three 4s). '0 0' means no bid yet.")
    history = dspy.InputField(desc="History of all bids made so far")
    action = dspy.OutputField(desc="Your action - must be either '[Bid] quantity face_value' (e.g. '[Bid] 3 4') or '[Call]'")

@METRIC_REGISTRY.register("liars_dice_bid_validation")
def validate_bid(example, prediction, trace=None):
    """Validate that the bid is properly formatted"""
    action = prediction.action.strip()
    if action == "[Call]":
        return 1
    
    if not action.startswith("[Bid] "):
        return 0
        
    try:
        _, quantity, face = action.split()
        quantity = int(quantity)
        face = int(face)
        if quantity < 1 or face < 1 or face > 6:
            return 0
        return 1
    except:
        return 0

class MakeBidModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.make_bid = dspy.ChainOfThought(MakeBidSignature)

    def forward(self, dice_roll, current_bid, history):
        return self.make_bid(
            dice_roll=dice_roll,
            current_bid=current_bid, 
            history=history
        )

@PLAYER_REGISTRY.register("liars_dice", "liars_dice_player")
class LiarsDicePlayer(Player):
    def init_actions(self):
        return {
            "MakeBid": MakeBidModule()
        }

from zero_sum_eval.player import Player
import dspy
from zero_sum_eval.registry import PLAYER_REGISTRY, LM_REGISTRY



class NextMove(dspy.Signature):
    """Given a code snippit, role, and context, produce a code snippit or annotation"""
    
    code = dspy.InputField(desc="The current code")
    role = dspy.InputField(desc="role of the player making the next move")
    context = dspy.InputField(desc="further context for the player")
    move = dspy.OutputField(desc="a valid base python expression or comment")


class CrackMeCoT(dspy.Module):

    def __init__(self):
        super().__init__()
        self.prog = dspy.Predict(NextMove)
    
    def forward(self, code, role, context):
        return self.prog(code=code,role=role,context=context)



@PLAYER_REGISTRY.register("crackme", "crackme_player")
class CrackMePlayer(Player):
    def __init__(self, lm, max_tries=4, **kwargs):
        super().__init__(**kwargs)
        lm_args = lm["args"] if "args" in lm else {}
        self.llm_model = LM_REGISTRY.build(lm["type"], **lm_args)
        self.max_tries = max_tries
        self.module = CrackMeCoT()

    def make_move(self, game_state):
        """
        Abstract method for making a move based on the current game state.
        
        Parameters:
        game_state (GameState): The current state of the game
        
        Returns:
        str: The move made by the player
        """

        code = {game_state.environment.get('code','')
        role = f"{game_state.roles}" 
        context = f"{game_state.context}"

        with dspy.context(lm=self.llm_model):
                trace = self.module(code, role, context)
        return trace.move
    


import dspy

from zero_sum_eval.core.player import Player
from zero_sum_eval.core.registry import PLAYER_REGISTRY

# Player keys
FOR_KEY = "for"
AGAINST_KEY = "against"

class OpeningStatementSignature(dspy.Signature):
    """You are an expert debater crafting a compelling opening statement for a debate. 
    Your role is to introduce your side's position in a clear, engaging, and persuasive manner."""
    
    topic: str = dspy.InputField(desc="The central issue or resolution being debated. Clearly state the topic to ensure focus.")
    side: str = dspy.InputField(desc="The position you are advocating for in this debate ('for' or 'against').")
    opening_statement: str = dspy.OutputField(desc=(
        "A well-structured and persuasive opening statement that introduces your side's position. "
        "The statement should establish a clear thesis, outline key arguments, and appeal to the audience. "
        "It should be concise, logical, and capture attention immediately."
    ))

class RebuttalSignature(dspy.Signature):
    """You are an expert debater crafting a rebuttal in response to the opposing side’s arguments. 
    Your role is to directly address their claims, refute weaknesses, and reinforce your position."""
    
    topic: str = dspy.InputField(desc="The central issue or resolution being debated. Ensure your rebuttal focuses on this topic.")
    side: str = dspy.InputField(desc="The position you are advocating for in this debate ('for' or 'against').")
    history: str = dspy.InputField(desc=(
        "The history of the debate so far, including key points, arguments, and rebuttals made by both sides. "
        "Use this context to identify weaknesses in the opposing side’s arguments and strategically strengthen your own position."
    ))
    rebuttal: str = dspy.OutputField(desc=(
        "A well-reasoned and persuasive rebuttal that directly addresses the arguments presented by the opposing side. "
        "It should identify logical flaws, counter with evidence, and reinforce your side's stance. The rebuttal should be respectful, "
        "concise, and highly effective in undermining the opposing side’s claims while advancing your argument."
    ))

class ClosingStatementSignature(dspy.Signature):
    """You are an expert debater crafting a powerful closing statement for a debate. 
    Your role is to summarize your side's position, highlight the strengths of your arguments, and make a lasting impression."""
    
    topic: str = dspy.InputField(desc="The central issue or resolution being debated. Make sure the closing statement ties back to this topic.")
    side: str = dspy.InputField(desc="The position you are advocating for in this debate ('for' or 'against').")
    history: str = dspy.InputField(desc=(
        "The history of the debate so far, including arguments, rebuttals, and counterarguments made by both sides. "
        "Use this context to synthesize key points and reinforce the validity of your side’s stance."
    ))
    closing_statement: str = dspy.OutputField(desc=(
        "A concise, compelling, and persuasive closing statement that summarizes the strongest aspects of your argument. "
        "It should address key points raised during the debate, refute remaining weaknesses in the opposing side's position, and leave the audience "
        "or judge with a clear understanding of why your side has prevailed. The statement should end on a strong, memorable note."
    ))


class OpeningStatement(dspy.Module):
    def __init__(self):
        self.make_opening_statement = dspy.ChainOfThought(OpeningStatementSignature)

    def forward(self, topic, side):
        return self.make_opening_statement(topic=topic, side=side)

class Rebuttal(dspy.Module):
    def __init__(self):
        self.make_rebuttal = dspy.ChainOfThought(RebuttalSignature)

    def forward(self, topic, history, side):
        return self.make_rebuttal(topic=topic, side=side, history=history)

class ClosingStatement(dspy.Module):
    def __init__(self):
        self.make_closing_statement = dspy.ChainOfThought(ClosingStatementSignature)

    def forward(self, topic, history, side):
        return self.make_closing_statement(topic=topic, side=side, history=history)


@PLAYER_REGISTRY.register("debate", "debate_player")
class DebatePlayer(Player):
    def init_actions(self):
        return {
            "OpeningStatement": OpeningStatement(),
            "Rebuttal": Rebuttal(),
            "ClosingStatement": ClosingStatement()
        }

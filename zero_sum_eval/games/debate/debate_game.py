import random
import json

from zero_sum_eval.type_definitions import Move
from zero_sum_eval.games.debate.debate_player import DebatePlayer, FOR_KEY, AGAINST_KEY
from zero_sum_eval.game_state import Action, GameState, PlayerDefinition, InvalidMoveError
from zero_sum_eval.registry import GAME_REGISTRY, LM_REGISTRY
from typing import Dict, List, Optional, Union
import dspy
from dspy import Prediction
from .debate_judge import DebateJudge, RubricWeights

@GAME_REGISTRY.register("debate")
class DebateGame(GameState):
    """
    This is a two-player game where the players take turns to make moves in a debate.
    """ 
    
    def __init__(
        self,
        rebuttal_rounds: int = 1,
        judges: list[Dict] = [
            {
                "name": "gpt-4o",
                "model": "openrouter/openai/gpt-4o",
            },
            {
                "name": "claude-3.5-sonnet",
                "model": "openrouter/anthropic/claude-3.5-sonnet-20240620",
            },
        ],
        rubric_weights: Dict = None,
        topics: Union[str, List[str]] = "topics.txt",
        topic: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        # If a topic is provided, use it. Otherwise, choose a random topic from the topics file/list
        if topic:
            self.topic = topic
        else:
            # path to the topic file
            if isinstance(topics, str):
                with open(topics, "r") as f:
                    self.topics = [line.strip() for line in f]
            else:
                self.topics = topics

            self.topic = random.choice(self.topics)

        self.history = []
        self.rebuttal_rounds = rebuttal_rounds
        self.rubric_weights = RubricWeights(**rubric_weights) if rubric_weights else RubricWeights()
        self.judge_module = DebateJudge(weights=self.rubric_weights)

        self._init_judges(judges)

        self.evaluations = None
        self.scores = {FOR_KEY: 0, AGAINST_KEY: 0}
        self.verdict = None

    def _init_judges(self, judges: List[Dict]) -> None:
        self.llm_judges = []
        for lm in judges:
            lm_args = lm["args"] if "args" in lm else {}
            if "type" not in lm:
                llm_model = dspy.LM(model=lm["model"], **lm_args)
            else:
                llm_model = LM_REGISTRY.build(lm["type"], **lm_args)

            self.llm_judges.append(llm_model)

    def update_game(self, move: Move):
        self.history.append(
            {
                "action": self.get_next_action().name + " | " + self.get_next_action().player.player_key,
                "move": move.value,
            }
        )
        # If the next action is the last, then the judges will decide the verdict
        if self.get_next_action().name == "ClosingStatement" and len(self.history) == 2 + (self.rebuttal_rounds * 2) + 2:
            self.verdict = self.judge()

    def is_over(self) -> bool:
        return self.verdict is not None

    def get_scores(self):
        if self.is_over():
            return {FOR_KEY: 1, AGAINST_KEY: 0} if self.verdict == "ForWin" else {FOR_KEY: 0, AGAINST_KEY: 1}
        return {FOR_KEY: 0, AGAINST_KEY: 0}

    def judge(self):
        for_score, against_score = 0, 0
        evaluations = {}
        for llm_judge in self.llm_judges:
            with dspy.context(lm=llm_judge):
                for_evaluation = self.judge_module(
                    topic=self.topic,
                    history=self.history,
                    side=FOR_KEY,
                )
                for_score += for_evaluation.weighted_score

                against_evaluation = self.judge_module(
                    topic=self.topic,
                    history=self.history,
                    side=AGAINST_KEY,
                )
                against_score += against_evaluation.weighted_score

                evaluations[llm_judge.model] = {
                    FOR_KEY: for_evaluation.toDict(),
                    AGAINST_KEY: against_evaluation.toDict(),
                }

        self.evaluations = evaluations
        self.scores = {FOR_KEY: for_score, AGAINST_KEY: against_score}
        
        if for_score > against_score:
            return "ForWin"
        elif for_score < against_score:
            return "AgainstWin"
        else:
            return "Tie"

    def get_next_action(self) -> Action:
        # The first side to make a move is the "for" side
        side = FOR_KEY if len(self.history) % 2 == 0 else AGAINST_KEY

        # The first 2 moves are opening statements
        if len(self.history) < 2:
            return Action("OpeningStatement", self.players[side])
        
        # The next 2 * rebuttal_rounds moves are rebuttals
        elif len(self.history) >= 2 and len(self.history) < 2 + (self.rebuttal_rounds * 2):
            return Action("Rebuttal", self.players[side])
        
        # The last 2 moves are closing statements
        else:
            return Action("ClosingStatement", self.players[side])

    def formatted_move_history(self) -> str:
        history = self.history
        formatted_history = ""
        for entry in history:
            formatted_history += f"==== {entry['action']} ===\n{entry['move']}\n\n"
        return formatted_history

    def player_inputs(self) -> Dict[str, str]:
        inputs = {
            "topic": self.topic,
            "side": self.get_next_action().player.player_key,
        }
        # history is passed to the player only if the next action is not an opening statement
        if not self.get_next_action().name == "OpeningStatement":
            inputs["history"] = self.formatted_move_history()
        
        return inputs

    def player_definitions(self) -> List[PlayerDefinition]:
        return [
            PlayerDefinition(player_key=FOR_KEY, actions=["OpeningStatement", "Rebuttal", "ClosingStatement"], default_player_class=DebatePlayer),
            PlayerDefinition(player_key=AGAINST_KEY, actions=["OpeningStatement", "Rebuttal", "ClosingStatement"], default_player_class=DebatePlayer),
        ]

    def display(self) -> str:
        display_str = f"Action: {self.get_next_action().name}, Side: {self.get_next_action().player.player_key}"
        display_str += f"\nTopic: {self.topic}"
        display_str += f"\nHistory:\n{self.formatted_move_history()}"
        if self.verdict:
            display_str += f"\n\nJudge Evaluations:"
            for judge, evaluation in self.evaluations.items():
                display_str += f"\n\nJudge: {judge}"
                display_str += f"\nFor: {json.dumps(evaluation[FOR_KEY], indent=4)}"
                display_str += f"\n\nAgainst: {json.dumps(evaluation[AGAINST_KEY], indent=4)}"
                display_str += f"\n\n===================="
            display_str += f"\nAggregated Scores:"
            display_str += f"\nFor: {self.scores[FOR_KEY]}"
            display_str += f"\nAgainst: {self.scores[AGAINST_KEY]}"
            display_str += f"\nFinal Verdict: {self.verdict}"
        return display_str

    def export(self):
        return {
            "formatted_history": self.formatted_move_history(),
            "topic": self.topic,
            "verdict": self.verdict,
            "evaluations": self.evaluations,
            "next_action": self.get_next_action().name + " " + self.get_next_action().player.player_key,
            "scores": self.get_scores(),
        }

from dataclasses import dataclass
import random
from litellm import deepcopy
from zero_sum_eval.game_state import GameState
from zero_sum_eval.registry import GAME_REGISTRY, LM_REGISTRY
from typing import Dict, List, Optional, Union
import dspy
from dspy import Prediction
from .debate_judge import DebateJudge, RubricWeights

@GAME_REGISTRY.register("debate")
class DebateGame(GameState):
    def instantiate(
        self,
        environment: dict,
        context: dict,
        roles: list[str],
        rebuttal_rounds: int = 1,
        judges: list[Dict] = [],
        rubric_weights: Dict = None,
        topics: Union[str, List[str]] = [],
    ) -> None:
        if roles:
            self.roles = roles
        else:
            self.roles = ["OpeningStatementFor", "OpeningStatementAgainst"]
            for _ in range(rebuttal_rounds):
                self.roles.extend(["RebuttalFor", "RebuttalAgainst"])
            self.roles.extend(["ClosingStatementFor", "ClosingStatementAgainst"])

         # path to the topic file
        if isinstance(topics, str):
            with open(topics, "r") as f:
                self.topics = [line.strip() for line in f]
        else:
            self.topics = topics

        self.environment = (
            environment
            if environment
            else {"topic": random.choice(self.topics), "side": "for", "history": [], "verdict": None}
        )
        self.context = context if context else {"message": None}
        self.rebuttal_rounds = rebuttal_rounds
        self.rubric_weights = (
            RubricWeights(**rubric_weights) if rubric_weights else RubricWeights()
        )
        self.judge_module = DebateJudge(weights=self.rubric_weights)
        self._init_judges(judges)

    def _init_judges(self, judges: List[Dict]) -> None:
        self.llm_judges = []
        for lm in judges:
            lm_args = lm["args"] if "args" in lm else {}
            if "type" not in lm:
                llm_model = dspy.LM(model=lm["model"], **lm_args)
            else:
                llm_model = LM_REGISTRY.build(lm["type"], **lm_args)

            self.llm_judges.append(llm_model)

    def update_game(self, move: str, trace: Optional[Prediction] = None) -> GameState:
        new_state = DebateGame(topics=self.topics)
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy(),
            rebuttal_rounds=self.rebuttal_rounds,
            topics=self.topics,
        )
        new_state.llm_judges = self.llm_judges
        new_state.rubric_weights = self.rubric_weights

        current_role = new_state.roles[0]
        new_state.environment["history"].append(
            {
                "role": current_role,
                "move": move,
                "last_trace": trace.toDict() if trace else None,
            }
        )
        new_state.environment["side"] = (
            "for" if current_role.endswith("For") else "against"
        )

        if len(new_state.roles) > 1:
            new_state.roles = new_state.get_next_roles()

        # If the current role is the last role, then the judges will decide the verdict
        if current_role == "ClosingStatementAgainst":
            new_state.environment["verdict"] = new_state.judge()

        return new_state

    def query_game(self) -> GameState:
        new_state = DebateGame(topics=self.topics)
        new_state.instantiate(
            self.environment.copy(),
            self.context.copy(),
            self.roles.copy(),
            rebuttal_rounds=self.rebuttal_rounds,
        )
        new_state.llm_judges = self.llm_judges
        new_state.rubric_weights = self.rubric_weights

        return new_state

    def judge(self):
        for_score, against_score = 0, 0
        evaluations = {}
        for llm_judge in self.llm_judges:
            with dspy.context(lm=llm_judge):

                for_evaluation = self.judge_module(
                    topic=self.environment["topic"],
                    history=self.environment["history"],
                    side="for",
                )
                for_score += for_evaluation.weighted_score

                against_evaluation = self.judge_module(
                    topic=self.environment["topic"],
                    history=self.environment["history"],
                    side="against",
                )
                against_score += against_evaluation.weighted_score

                evaluations[llm_judge.model] = {
                    "for": for_evaluation.toDict(),
                    "against": against_evaluation.toDict(),
                }

        self.environment["evaluations"] = evaluations

        if for_score > against_score:
            return "ForWin"
        elif for_score < against_score:
            return "AgainstWin"
        else:
            return "Tie"

    def validate_game(self) -> Optional[str]:
        if self.environment["verdict"] is not None:
            return self.environment["verdict"]
        return None

    def get_next_roles(self) -> List[str]:
        return self.roles[1:]

    def formatted_move_history(self) -> str:
        history = self.environment["history"]
        formatted_history = ""
        for entry in history:
            formatted_history += f"==== {entry['role']} ===\n{entry['move']}\n\n"
        return formatted_history

    def player_inputs(self) -> Dict[str, str]:
        current_role = self.roles[0]
        if current_role.startswith("OpeningStatement"):
            return {"topic": self.environment["topic"], "role": current_role}
        elif current_role.startswith("Rebuttal") or current_role.startswith(
            "ClosingStatement"
        ):
            return {
                "topic": self.environment["topic"],
                "history": self.formatted_move_history(),
                "role": current_role,
            }
        elif current_role == "Judge":
            return {
                "topic": self.environment["topic"],
                "history": self.formatted_move_history(),
                "role": current_role,
            }
        else:
            raise ValueError(f"Role {current_role} not recognized")

    def display(self) -> None:
        display_str = f"Role to Act: {self.roles[0]}"
        display_str += f"\nTopic: {self.environment['topic']}"
        display_str += f"\nSide: {self.environment['side']}"
        display_str += f"\nHistory:\n{self.formatted_move_history()}"
        return display_str

    def export(self) -> str:
        return {
            "environment": deepcopy(self.environment),
            "roles": self.roles.copy(),
            "formatted_history": self.formatted_move_history(),
            "validate_game": self.validate_game(),
        }

# the code for the attacker
import os
from functools import partial
import openai
import json
import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from zero_sum_eval.pyjail.verification import verify_solution
from zero_sum_eval.pyjail.dummy_challenge import challenge, code
from zero_sum_eval.pyjail.attacker_dspy import AttackerCoT


def valid_json(input_str):
    """Checks if a string can be parsed as valid json"""
    try:
        json.loads(input_str)
        return True
    except json.JSONDecodeError:
        return False


class CTFChallenge(dspy.Signature):
    """Given an example of CTF challenge and the corresonding code, produce code for a new challenge"""

    challenge = dspy.InputField(desc="description of a capture the flag challenge")
    code = dspy.InputField(desc="code from the ctf challenge")
    new_code = dspy.OutputField(desc="code for a new ctf challenge")


# class SolutionJson(dspy.Signature):
#     """Given a rationale and solution, produce a json object with key "solution" containing the code to extract the flag"""

#     rationale = dspy.InputField(desc="rationale of the solution")
#     solution = dspy.InputField(desc="description of the solution")
#     solution_json = dspy.OutputField(desc='json with key "solution"')


class DefenderCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot = dspy.ChainOfThought(CTFChallenge)
        
        self.attacker = assert_transform_module(
            AttackerCoT(), partial(backtrack_handler, max_backtracks=5)
        )

    def forward(self, challenge, code):
        cot = self.cot(challenge=challenge, code=code)
        # solution_json = self.output_json(rationale=cot.rationale, solution=cot.solution)
        # dspy.Assert(
        #     valid_json(solution_json.solution_json),
        #     "Final output should be parseable json.",
        # )
        return cot


if __name__ == "__main__":
    openai.api_type = "azure"
    openai.api_base = "https://allam-arabic-data-cleaning.openai.azure.com/"  # "https://gpt4rnd.openai.azure.com/"
    openai.api_version = "2024-02-15-preview"  # "2023-07-01-preview"
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Set up the LM
    gpt4 = dspy.AzureOpenAI(
        api_base=openai.api_base,
        api_version=openai.api_version,
        api_key=openai.api_key,
        deployment_id="GPT-4-new",  # "gpt-35-haidar",
        max_tokens=800,
        temperature=0.8,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )
    dspy.settings.configure(lm=gpt4)
    dspy.configure(trace=[])

    defender = assert_transform_module(
        DefenderCoT(), partial(backtrack_handler, max_backtracks=5)
    )
    defender_trace = defender(challenge=challenge, code=code)
    print(gpt4.inspect_history(n=5))
    # try:
    #     attacker_solution = json.loads(defender_trace.solution_json)["solution"]
    # except json.JSONDecodeError:
    #     print("Unable to parse the JSON string!")
    #     attacker_solution = ""
    # print(f"\n\nSubmitting the solution : {attacker_solution}")
    # result = verify_solution(attacker_solution, verbose=False)

    # if result:
    #     print("(+)\tSuccessfully retrieved the flag!")
    # else:
    #     print("(-)\tFailed to retrieve the flag!")
    # print()

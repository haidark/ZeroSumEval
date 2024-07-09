# the code for the attacker
import os
from functools import partial
import openai
import json
import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from zero_sum_eval.games.pyjail.verification import verify_solution
from zero_sum_eval.games.pyjail.dummy_challenge import challenge, code, code2


def valid_json(input_str):
    """Checks if a string can be parsed as valid json"""
    try:
        json.loads(input_str)
        return True
    except json.JSONDecodeError:
        return False


class CTFSolution(dspy.Signature):
    """Given a CTF challenge and the corresonding code, produce a solution"""

    challenge = dspy.InputField(desc="description of a capture the flag challenge")
    code = dspy.InputField(desc="code from the ctf challenge")
    solution = dspy.OutputField(desc="description of the solution")


class SolutionJson(dspy.Signature):
    """Given a rationale and solution, produce a json object with key "solution" containing the code to extract the flag"""

    rationale = dspy.InputField(desc="rationale of the solution")
    solution = dspy.InputField(desc="description of the solution")
    solution_json = dspy.OutputField(desc='json with key "solution"')


class AttackerCoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot = dspy.ChainOfThought(CTFSolution)
        self.output_json = dspy.Predict(SolutionJson)

    def forward(self, challenge, code):
        cot = self.cot(challenge=challenge, code=code)
        solution_json = self.output_json(rationale=cot.rationale, solution=cot.solution)
        dspy.Assert(
            valid_json(solution_json.solution_json),
            "Final output should be parseable json.",
        )
        return solution_json


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

    attacker = assert_transform_module(
        AttackerCoT(), partial(backtrack_handler, max_backtracks=5)
    )
    attacker_trace = attacker(challenge=challenge, code=code2)
    print(gpt4.inspect_history(n=5))
    try:
        attacker_solution = json.loads(attacker_trace.solution_json)["solution"]
    except json.JSONDecodeError:
        print("Unable to parse the JSON string!")
        attacker_solution = ""
    print(f"\n\nSubmitting the solution : {attacker_solution}")
    result = verify_solution(attacker_solution, verbose=False)

    if result:
        print("(+)\tSuccessfully retrieved the flag!")
    else:
        print("(-)\tFailed to retrieve the flag!")
    print()
    # # make the dspy example

    # ctf_challenge = dspy.Example(
    #     challenge=challenge,
    #     code=code,
    #     solution_json="""open("/flag.txt", 'r').read()""",
    # ).with_inputs("challenge", "code")

    # trainset = [ctf_challenge]

    # # Set up the optimizer: we want to "bootstrap" (i.e., self-generate) 8-shot examples of your program's steps.
    # # The optimizer will repeat this 10 times (plus some initial attempts) before selecting its best attempt on the devset.
    # config = dict(max_bootstrapped_demos=3, max_labeled_demos=3, num_candidate_programs=10, num_threads=4)

    # teleprompter = BootstrapFewShotWithRandomSearch(metric=submit_solution, **config)
    # optimized_program = teleprompter.compile(attacker, trainset=trainset)

# Note: The openai-python library support for Azure OpenAI is in preview.
# Note: This code sample requires OpenAI Python library version 0.28.1 or lower.
# https://gpt4rnd.openai.azure.com/openai/deployments/gpt-35-haidar/chat/completions?api-version=2023-07-01-preview
# oai key: 20cde2d0638e43d5aec14d531a2c0baf
import os
import openai
import dspy
from dspy.datasets.gsm8k import GSM8K, gsm8k_metric

openai.api_type = "azure"
openai.api_base = "https://gpt4rnd.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = os.getenv("OPENAI_API_KEY")


# Set up the LM
turbo = dspy.AzureOpenAI(
    api_base=openai.api_base,
    api_version=openai.api_version,
    api_key=openai.api_key,
    deployment_id="gpt-35-haidar",
    max_tokens=250,
)
dspy.settings.configure(lm=turbo)

# Load math questions from the GSM8K dataset
gms8k = GSM8K()
gsm8k_trainset, gsm8k_devset = gms8k.train[:10], gms8k.dev[:10]


class CoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought("question -> answer")

    def forward(self, question):
        return self.prog(question=question)


from dspy.teleprompt import BootstrapFewShot

# Set up the optimizer: we want to "bootstrap" (i.e., self-generate) 4-shot examples of our CoT program.
config = dict(max_bootstrapped_demos=4, max_labeled_demos=4)

# Optimize! Use the `gms8k_metric` here. In general, the metric is going to tell the optimizer how well it's doing.
teleprompter = BootstrapFewShot(metric=gsm8k_metric, **config)
optimized_cot = teleprompter.compile(
    CoT(), trainset=gsm8k_trainset, valset=gsm8k_devset
)

from dspy.evaluate import Evaluate

# Set up the evaluator, which can be used multiple times.
evaluate = Evaluate(
    devset=gsm8k_devset,
    metric=gsm8k_metric,
    num_threads=4,
    display_progress=True,
    display_table=0,
)

# Evaluate our `optimized_cot` program.
evaluate(optimized_cot)

print(turbo.inspect_history(n=1))

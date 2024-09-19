import json
from pathlib import Path
import re
import argparse
import re


def extract_gsm8k(example):
    question = example["question"]
    answer = example["answer"].split("####")[-1].strip()
    return question, answer

def extract_hendrycks_math(example):
    question = example['problem']
    boxed_content =  re.search(r'\\boxed\{(.*?)\}', example['solution'])
    answer = boxed_content.group(1) if boxed_content else None
    answer = answer if answer and answer.replace('.', '').isdigit() else None

    return question, answer

def extract_examples(input_file, dataset_name):
    # Load the dataset
    examples = []
    if dataset_name == 'math':
        extractor = extract_hendrycks_math
    else:
        extractor = extract_gsm8k
    
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            examples.append(json.loads(line))

    # Extract examples (questions and answers)
    extracted_examples = []
    for example in examples:
        question, answer = extractor(example)
        if answer:
            extracted_examples.append({
                "question": question,
                "answer": answer
            })

    num_examples = min(1000, len(extracted_examples))  # Adjust the number of examples as needed

    extracted_output = Path(input_file).parent / f"mathquiz_{dataset_name}_examples.jsonl"
    with open(extracted_output, "w", encoding="utf-8") as f:
        for example in extracted_examples[:num_examples]:
            json.dump(example, f)
            f.write("\n")

    print(f"Extracted {num_examples} examples saved to {extracted_output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract examples from math datasets")
    parser.add_argument("dataset_name", type=str, choices=["gsm8k", "hendrycks-math"], help="Name of the dataset (gsm8k or math)")
    args = parser.parse_args()

    input_file_path = Path(__file__).parent / f"{args.dataset_name}_train.jsonl"
    if not input_file_path.exists():
        print(f"Error: Input file '{input_file_path}' does not exist.")
        exit(1)

    extract_examples(input_file_path, args.dataset_name)
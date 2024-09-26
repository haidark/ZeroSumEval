import json
from pathlib import Path
import re
import argparse
import re


def extract_prompt_injection(example):

    def extract_password(text):
        # Use a regular expression to find the password in single or double quotes
        match = re.search(r'["\'](.*?)["\']', text)
        if match:
            res = match.group(1)
            if ' ' in res:
                return None
            return res
        
        return None

    secret = extract_password(example['test_case_prompt'])
    infiltrator_response = example['user_input']
    sentinel_response = ""

    return secret, infiltrator_response, sentinel_response

def extract_examples(input_file, dataset_name):
    # Load the dataset
    examples = []
    if dataset_name == 'cyberseceval':
        extractor = extract_prompt_injection
        with open(input_file, "r", encoding="utf-8") as f:
            objs = json.load(f)
            for obj in objs:
                if obj['injection_type'] == 'direct' and 'anyone' in obj['test_case_prompt']:
                    examples.append(obj)

    # Extract examples (questions and answers)
    extracted_examples = []
    for example in examples:
        secret, infiltrator_response, sentinel_response = extractor(example)
        if secret:
            extracted_examples.append({
                "secret_password": secret,
                "infiltrator_response": infiltrator_response,
                "sentinel_response": sentinel_response
            })

    num_examples = min(1000, len(extracted_examples))  # Adjust the number of examples as needed

    extracted_output = Path(input_file).parent / f"gandalf_{dataset_name}_examples.jsonl"
    with open(extracted_output, "w", encoding="utf-8") as f:
        for example in extracted_examples[:num_examples]:
            json.dump(example, f)
            f.write("\n")

    print(f"Extracted {num_examples} examples saved to {extracted_output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract examples from gandalf-type datasets")
    parser.add_argument("dataset_name", type=str, choices=["cyberseceval"], help="Name of the dataset")
    args = parser.parse_args()
    if args.dataset_name == "cyberseceval":
        input_file_path = Path(__file__).parent / f"prompt_injection.json"
    
    if not input_file_path.exists():
        print(f"Error: Input file '{input_file_path}' does not exist.")
        exit(1)

    extract_examples(input_file_path, args.dataset_name)
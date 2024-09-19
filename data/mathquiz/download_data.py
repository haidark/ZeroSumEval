import json
import argparse
from datasets import load_dataset
from pathlib import Path

def download_gsm8k():
    dataset = load_dataset("gsm8k", "main")
    train_data = dataset["train"]
    output_file = Path(__file__).parent / "gsm8k_train.jsonl"
    
    with open(output_file, "w", encoding="utf-8") as f:
        for example in train_data:
            json.dump(example, f)
            f.write("\n")
    
    print(f"GSM8K training set saved to {output_file}")

def download_math():
    dataset = load_dataset("hendrycks/competition_math")
    train_data = dataset["train"]
    output_file = Path(__file__).parent / "hendrycks-math_train.jsonl"
    
    with open(output_file, "w", encoding="utf-8") as f:
        for example in train_data:
            json.dump(example, f)
            f.write("\n")
    
    print(f"MATH training set saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download GSM8K or MATH dataset")
    parser.add_argument("dataset", choices=["gsm8k", "math"], help="Choose which dataset to download: 'gsm8k' or 'math'")
    args = parser.parse_args()

    if args.dataset == "gsm8k":
        download_gsm8k()
    elif args.dataset == "math":
        download_math()

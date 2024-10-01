import requests
import json
import argparse
from datasets import load_dataset
from pathlib import Path

def download_cyberseceval():
    url = "https://github.com/meta-llama/PurpleLlama/raw/refs/heads/main/CybersecurityBenchmarks/datasets/prompt_injection/prompt_injection.json"
    output_path = Path(__file__).parent / "prompt_injection.json"
    
    response = requests.get(url)
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    print(f"CyberSecEval prompt injection dataset downloaded to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download jailbreaking datasets")
    parser.add_argument("dataset", choices=["cyberseceval",], help="Choose which dataset to download.")
    args = parser.parse_args()

    if args.dataset == "cyberseceval":
        download_cyberseceval()

import json
from pathlib import Path
import random
import argparse

def extract_examples(input_file, dataset_name):
    # Load the dataset
    examples = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            examples.append(json.loads(line))

    # Extract examples (questions and answers)
    teacher_examples = []
    student_examples = []
    for example in examples:
        question = example["question"]
        answer = example["answer"].split("####")[-1].strip()
        teacher_examples.append({
            "role": "TeacherGenerateQuestion",
            "message": "Generate a math question",
            "target": answer,
            "math_question": question
        })
        student_examples.append({
            "role": "StudentAnswerQuestion",
            "message": "Answer the following math question",
            "question": question,
            "answer": answer
        })

    num_examples = min(1000, len(teacher_examples))  # Adjust the number of examples as needed

    # Save teacher examples
    teacher_output = Path(input_file).parent / f"mathquiz_{dataset_name}_teacher_examples.jsonl"
    with open(teacher_output, "w", encoding="utf-8") as f:
        for example in teacher_examples[:num_examples]:
            json.dump(example, f)
            f.write("\n")

    # Save student examples
    student_output = Path(input_file).parent / f"mathquiz_{dataset_name}_student_examples.jsonl"
    with open(student_output, "w", encoding="utf-8") as f:
        for example in student_examples[:num_examples]:
            json.dump(example, f)
            f.write("\n")

    print(f"Extracted {num_examples} examples for teacher and student")
    print(f"Teacher examples saved to {teacher_output}")
    print(f"Student examples saved to {student_output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract examples from math datasets")
    parser.add_argument("dataset_name", type=str, choices=["gsm8k", "math"], help="Name of the dataset (gsm8k or math)")
    args = parser.parse_args()

    input_file_path = Path(__file__).parent / f"{args.dataset_name}_train.jsonl"
    if not input_file_path.exists():
        print(f"Error: Input file '{input_file_path}' does not exist.")
        exit(1)

    extract_examples(input_file_path, args.dataset_name)
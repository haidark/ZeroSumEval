import tempfile
from unittest.mock import patch
import json

from zero_sum_eval.main import cli_run

class MockLM:
    def __init__(self, *args, **kwargs):
        self.model = kwargs.get('model', 'mock-model')
        self.kwargs = {
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        
    def __call__(self, messages=None, prompt=None, **kwargs):
        # Handle both messages and prompt-based calls
        if messages is not None:
            # For chat-based models
            response = self._get_response(str(messages))
        elif prompt is not None:
            # For completion-based models
            response = self._get_response(prompt)
        else:
            raise ValueError("Either messages or prompt must be provided")
            
        # Return response as a JSON string
        return [json.dumps(response)]
    
    def _get_response(self, input_text):
        # Return predetermined responses based on input
        if "GenerateQuestion" in input_text or "target" in input_text:
            return {
                "rationale": "Let me create a simple multiplication question.",
                "question": "What is 6 times 7?"
            }
        elif "AnswerQuestion" in input_text or "What is" in input_text:
            return {
                "rationale": "The answer is straightforward.",
                "answer": "42"
            }
        # Default response for question generation
        return {
            "rationale": "Let me create a simple addition question.",
            "question": "What is 2 plus 2?"
        }

def test_complete_mathquiz_game(monkeypatch, cleanup_logging):
    """Test a complete mathquiz game from start to finish through the CLI."""
    # Create a temporary directory for outputs
    with tempfile.TemporaryDirectory(prefix="test_main") as temp_dir:
        # Mock the LLM to avoid API calls
        monkeypatch.setattr("dspy.LM", MockLM)
        
        # Set up CLI arguments for a mathquiz game
        test_args = [
            'main.py',
            '-g', 'mathquiz',  # Use mathquiz game
            '-p',              # Specify models for each player
            'teacher=mock-model',
            'student=mock-model',
            '-o', temp_dir,    # Use temp dir for outputs
            '--max_rounds', '3',         # Limit rounds
            '--max_player_attempts', '2'  # Limit retries
        ]
        
        # Run the game
        with patch('sys.argv', test_args):
            cli_run()

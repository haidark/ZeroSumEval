import pytest
import os
import json
import dspy
from zero_sum_eval.checkpointing import get_cached_module_path, save_checkpoint, load_checkpoint

def test_get_cached_module_path(temp_cache_dir):
    model = "gpt-4"
    action = "generate"
    optimizer = "dpo"
    dataset = "chess_dataset"
    optimizer_args = {"key1": "value1", "key2": "value2"}
    compilation_args = {"key3": "value3"}
    
    expected_path = os.path.join(
        temp_cache_dir,
        model,
        action,
        optimizer,
        dataset,
        "optimizer_args[key1=value1,key2=value2]_compilation_args[key3=value3].json"
    )
    
    actual_path = get_cached_module_path(
        model=model,
        action=action,
        optimizer=optimizer,
        dataset=dataset,
        optimizer_args=optimizer_args,
        compilation_args=compilation_args,
        cache_dir=temp_cache_dir
    )
    
    assert actual_path == expected_path

def test_get_cached_module_path_with_lm(temp_cache_dir):
    model = "gpt-4"
    action = "generate"
    optimizer = "dpo"
    dataset = "chess_dataset"
    lm = dspy.LM(model="gpt-4")
    optimizer_args = {"model": lm}
    
    expected_path = os.path.join(
        temp_cache_dir,
        model,
        action,
        optimizer,
        dataset,
        "optimizer_args[model=gpt-4]_compilation_args[].json"
    )
    
    actual_path = get_cached_module_path(
        model=model,
        action=action,
        optimizer=optimizer,
        dataset=dataset,
        optimizer_args=optimizer_args,
        cache_dir=temp_cache_dir
    )
    
    assert actual_path == expected_path

def test_save_checkpoint(temp_cache_dir, sample_module):
    path = os.path.join(temp_cache_dir, "test_checkpoint.json")
    
    # Create a mock save method for the sample module
    def mock_save(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write('{}')  # Write empty JSON object
    
    sample_module.save = mock_save
    save_checkpoint(sample_module, path)
    assert os.path.exists(path)

def test_load_checkpoint(temp_cache_dir, sample_module):
    path = os.path.join(temp_cache_dir, "test_checkpoint.json")
    
    # Create mock save/load methods
    def mock_save(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write('{}')
            
    def mock_load(path):
        with open(path, 'r') as f:
            pass  # Just verify we can read the file
    
    sample_module.save = mock_save
    sample_module.load = mock_load
    
    # Test loading non-existent checkpoint
    with pytest.raises(FileNotFoundError):
        load_checkpoint(sample_module, path)
    
    # Save and load checkpoint
    save_checkpoint(sample_module, path)
    loaded_module = load_checkpoint(sample_module, path)
    assert loaded_module is sample_module
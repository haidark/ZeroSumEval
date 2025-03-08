import pytest
import os
import tempfile
from zero_sum_eval.utils.config_utils import load_yaml_with_env_vars

def test_load_yaml_with_env_vars():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("""
        test_var: ${TEST_ENV_VAR}
        normal_var: normal_value
        """)
        f.flush()
        
        # Test with environment variable set
        os.environ['TEST_ENV_VAR'] = 'test_value'
        config = load_yaml_with_env_vars(f.name)
        assert config['test_var'] == 'test_value'
        assert config['normal_var'] == 'normal_value'
        
        # Test with environment variable not set
        del os.environ['TEST_ENV_VAR']
        config = load_yaml_with_env_vars(f.name)
        assert config['test_var'] == '${TEST_ENV_VAR}'
        assert config['normal_var'] == 'normal_value'
        
    os.unlink(f.name) 
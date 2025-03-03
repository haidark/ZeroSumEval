import pytest
from unittest.mock import MagicMock, patch
import dspy
from zero_sum_eval.player import Player, PlayerDefinition
from zero_sum_eval.type_definitions import ActionConfig, Action

class SimpleTestPlayer(Player):
    """A simple concrete implementation of Player for testing"""
    def init_actions(self):
        class TestModule(dspy.Module):
            def forward(self):
                return dspy.Prediction(extra="extra dspy output", output="dspy output")
        
        return {action.name: TestModule() for action in self.actions}

class TestNonDspyPlayer(Player):
    """Test implementation of Player with actions that are not dspy modules"""
    def init_actions(self):
        return {action.name: lambda **args: action.name for action in self.actions}

@pytest.fixture
def basic_lm_config():
    return {
        "model": "gpt-3.5-turbo",
        "args": {"api_key": "test-key"},
        "optimize": False
    }

@pytest.fixture
def basic_actions():
    return [
        ActionConfig(name="test_action1"),
        ActionConfig(name="test_action2", optimize=True, dataset="test_dataset")
    ]

def test_player_initialization(basic_lm_config, basic_actions):
    player = SimpleTestPlayer(
        id="test_player",
        actions=basic_actions,
        lm=basic_lm_config,
        player_key="test"
    )
    
    assert player.id == "test_player"
    assert player.player_key == "test"
    assert len(player.actions) == 2
    assert player.action_names == ["test_action1", "test_action2"]
    assert all(action in player.action_fn_dict for action in player.action_names)

def test_player_initialization_with_string_actions():
    actions = ["move", "evaluate"]
    player = SimpleTestPlayer(
        id="test_player",
        actions=actions,
        lm={"model": "gpt-3.5-turbo", "optimize": False},
        player_key="test"
    )
    
    assert len(player.actions) == 2
    assert all(isinstance(action, ActionConfig) for action in player.actions)
    assert player.action_names == actions

def test_player_abstract_class():
    with pytest.raises(TypeError):
        # Should raise error because Player is abstract
        Player(
            id="test",
            actions=["test"],
            lm={"model": "gpt-3.5-turbo"},
            player_key="test"
        )

def test_invalid_action_configuration():
    with pytest.raises(ValueError):
        SimpleTestPlayer(
            id="test_player",
            actions=[ActionConfig(name="test_action", optimize=True)],  # Missing dataset for optimization
            lm={"model": "gpt-3.5-turbo", "optimize": True},
            player_key="test"
        )

def test_player_definition():
    player_def = PlayerDefinition(
        player_key="test_player",
        actions=["move", "evaluate"],
        default_player_class=SimpleTestPlayer
    )
    
    assert player_def.player_key == "test_player"
    assert player_def.actions == ["move", "evaluate"]
    assert player_def.default_player_class == SimpleTestPlayer

@pytest.mark.parametrize("action_config", [
    ActionConfig(name="test", optimize=False),
    {"name": "test", "optimize": False},
    "test"
])
def test_different_action_formats(action_config, basic_lm_config):
    player = SimpleTestPlayer(
        id="test_player",
        actions=[action_config],
        lm=basic_lm_config,
        player_key="test"
    )
    
    assert len(player.actions) == 1
    assert isinstance(player.actions[0], ActionConfig)
    assert player.actions[0].name == "test"

def test_module_paths_loading(basic_lm_config):
    # Use patch instead of mocker
    with patch('zero_sum_eval.player.load_checkpoint') as mock_load:
        mock_load.return_value = MagicMock(spec=dspy.Module)
        
        lm_config = basic_lm_config.copy()
        lm_config["module_paths"] = {"test_action": "path/to/module"}
        
        player = SimpleTestPlayer(
            id="test_player",
            actions=["test_action"],
            lm=lm_config,
            player_key="test"
        )
        
        mock_load.assert_called_once()

def test_dspy_player(basic_lm_config):
    player = SimpleTestPlayer(
        id="test_player",
        actions=["test_action"],
        lm=basic_lm_config,
        player_key="test"
    )

    move = player.act(Action(name="test_action", player_key="test", inputs={}))
    assert move.value == "dspy output"
    assert move.trace.toDict() == {"extra": "extra dspy output", "output": "dspy output"}

def test_non_dspy_player():
    player = TestNonDspyPlayer(
        id="non_dspy",
        actions=["move"],
        lm={"model": "gpt-3.5-turbo", "optimize": False},
        player_key="non_dspy"
    )

    move = player.act(Action(name="move", player_key="non_dspy", inputs={}))
    assert move.value == "move"

def test_cached_module_loading(basic_lm_config):
    # Modify lm_config to enable optimization
    lm_config = basic_lm_config.copy()
    lm_config["optimize"] = True
    
    with patch('zero_sum_eval.player.get_cached_module_path') as mock_get_cached_path, \
         patch('zero_sum_eval.player.load_checkpoint') as mock_load_checkpoint, \
         patch('zero_sum_eval.player.save_checkpoint') as mock_save_checkpoint, \
         patch('zero_sum_eval.registry.DATASET_REGISTRY.build') as mock_dataset_build, \
         patch('zero_sum_eval.registry.METRIC_REGISTRY.build') as mock_metric_build, \
         patch('zero_sum_eval.registry.OPTIMIZER_REGISTRY.build') as mock_optimizer_build:
        
        # Setup mock returns
        mock_get_cached_path.return_value = "cached/path"
        mock_load_checkpoint.return_value = MagicMock(spec=dspy.Module)
        mock_dataset_build.return_value.get_dataset.return_value = []
        mock_dataset_build.return_value.output_key = "output"
        mock_metric_build.return_value = MagicMock()
        mock_optimizer_build.return_value = MagicMock()
        
        actions = [ActionConfig(
            name="test_action",
            optimize=True,
            dataset="test_dataset",
            dataset_args={},
            metric="test_metric"
        )]
        
        # Test successful cache loading
        player = SimpleTestPlayer(
            id="test_player",
            actions=actions,
            lm=lm_config,
            player_key="test",
            use_cache=True
        )
        
        mock_get_cached_path.assert_called_once()
        mock_load_checkpoint.assert_called_once()

def test_optimizer_configuration():
    """Test that optimizer configuration is properly handled"""
    lm_config = {
        "model": "gpt-3.5-turbo",
        "optimizer": "MIPROv2",
        "optimizer_args": {"custom_arg": "value"},
        "compilation_args": {"compile_arg": "value"},
        "optimize": True
    }
    
    with patch('zero_sum_eval.registry.DATASET_REGISTRY.build') as mock_dataset_build, \
         patch('zero_sum_eval.registry.METRIC_REGISTRY.build') as mock_metric_build, \
         patch('zero_sum_eval.registry.OPTIMIZER_REGISTRY.build') as mock_optimizer_build:
        
        # Setup mock returns
        mock_optimizer = MagicMock()
        mock_optimizer_build.return_value = mock_optimizer
        mock_dataset_build.return_value.get_dataset.return_value = []
        mock_dataset_build.return_value.output_key = "output"
        mock_metric_build.return_value = MagicMock()
        
        actions = [ActionConfig(
            name="test_action",
            optimize=True,
            dataset="test_dataset",
            dataset_args={},
            metric="test_metric"
        )]
        
        player = SimpleTestPlayer(
            id="test_player",
            actions=actions,
            lm=lm_config,
            player_key="test"
        )
        
        # Verify optimizer was built with correct arguments
        assert mock_optimizer_build.call_count == 1
        call_args = mock_optimizer_build.call_args[0]
        call_kwargs = mock_optimizer_build.call_args[1]
        
        # Check positional args
        assert call_args[0] == "MIPROv2"
        
        # Check keyword args
        assert call_kwargs["metric"] == mock_metric_build.return_value
        assert call_kwargs["custom_arg"] == "value"
        assert call_kwargs["prompt_model"] == player.llm_model
        assert call_kwargs["task_model"] == player.llm_model
        
        # Verify dataset and metric were built correctly
        mock_dataset_build.assert_called_with("test_dataset")
        mock_metric_build.assert_called_with("test_metric", output_key=mock_dataset_build.return_value.output_key)

def test_custom_optimizer_configuration():
    """Test configuration with a custom optimizer that doesn't need prompt/task models"""
    lm_config = {
        "model": "gpt-3.5-turbo",
        "optimizer": "CustomOptimizer",
        "optimizer_args": {"custom_arg": "value"},
        "compilation_args": {"compile_arg": "value"},
        "optimize": True
    }
    
    with patch('zero_sum_eval.registry.DATASET_REGISTRY.build') as mock_dataset_build, \
         patch('zero_sum_eval.registry.METRIC_REGISTRY.build') as mock_metric_build, \
         patch('zero_sum_eval.registry.OPTIMIZER_REGISTRY.build') as mock_optimizer_build:
        
        # Setup mock returns
        mock_optimizer = MagicMock()
        mock_optimizer_build.return_value = mock_optimizer
        mock_dataset_build.return_value.get_dataset.return_value = []
        mock_dataset_build.return_value.output_key = "output"
        mock_metric_build.return_value = MagicMock()
        
        actions = [ActionConfig(
            name="test_action",
            optimize=True,
            dataset="test_dataset",
            dataset_args={},
            metric="test_metric"
        )]
        
        player = SimpleTestPlayer(
            id="test_player",
            actions=actions,
            lm=lm_config,
            player_key="test"
        )
        
        # Verify optimizer was built with correct arguments
        assert mock_optimizer_build.call_count == 1
        call_args = mock_optimizer_build.call_args[0]
        call_kwargs = mock_optimizer_build.call_args[1]
        
        # Check positional args
        assert call_args[0] == "CustomOptimizer"
        
        # Check keyword args - should only have metric and custom_arg
        assert len(call_kwargs) == 2
        assert call_kwargs["metric"] == mock_metric_build.return_value
        assert call_kwargs["custom_arg"] == "value"
        
        # Verify dataset and metric were built correctly
        mock_dataset_build.assert_called_with("test_dataset")
        mock_metric_build.assert_called_with("test_metric", output_key=mock_dataset_build.return_value.output_key) 
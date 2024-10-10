import os
import yaml
import re


def load_yaml_with_env_vars(file_path):
    # Custom loader that expands environment variables
    def env_var_constructor(loader, node):
        value = loader.construct_scalar(node)
        return os.environ.get(value[2:-1], value)  # Remove ${ and }

    # Add the custom constructor to the yaml loader
    yaml.add_implicit_resolver("!env", re.compile(r"\$\{([^}^{]+)\}"), None, yaml.SafeLoader)
    yaml.add_constructor("!env", env_var_constructor, yaml.SafeLoader)

    # Load the YAML file
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
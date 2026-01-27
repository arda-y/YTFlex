"""
Module for reading the config.yaml file.

Use the get function to get the value of a setting.

config.yaml file is read seperately every time the get function is called to allow
hot swapping values without restarting the server on modification.
"""

import os
import yaml


def get(setting_name: str, default_value=None) -> any:
    """
    Basically an `os.getenv()` function but for the config.yaml file.

    Returns the value of a setting from the config.yaml file with the given `setting_name`.

    If the `setting_name` is not found, the `default_value` is returned if provided,
    otherwise `None` is returned.
    """

    this_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(this_dir, "config.yaml")

    with open(config_path, "r", encoding="UTF_8") as file:
        # safe_load is used to prevent code execution from the file
        cfg = yaml.safe_load(file)
        file.close()  # closing the file allows the file to be modified
    try:
        return cfg[setting_name]
    except KeyError:
        return default_value

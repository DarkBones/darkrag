import tomllib
from pathlib import Path


def load_settings() -> dict:
    """
    Load application settings from pyproject.toml.

    Returns:
        dict: Configuration settings under the tool.darkrag namespace
    """

    config_path = Path("pyproject.toml")
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    return config["tool"]["darkrag"]


settings = load_settings()

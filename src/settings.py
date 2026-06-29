from pathlib import Path
import os
import yaml
from dotenv import load_dotenv

# Sets the base project directory by moving one level up from the current script location
BASE_DIR = Path(__file__).resolve().parents[1]

# Defines the path to the YAML configuration file
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

# Loads environment variables from the .env file located in the project root
load_dotenv(BASE_DIR / ".env")

def load_config():
    # Opens the YAML configuration file in read mode
    with open(CONFIG_PATH, "r") as file:
        # Parses the YAML content into a Python dictionary and returns it
        return yaml.safe_load(file)

def get_env(name, required=True):
    # Retrieves the value of the specified environment variable
    value = os.getenv(name)

    # Checks if the variable is required but not found, and raises an error if so
    if required and not value:
        raise ValueError(f"Missing environment variable: {name}")

    # Returns the environment variable value (or None if not required and missing)
    return value

import os
import yaml
from yaml.loader import SafeLoader


def load_config(location="config"):
    config_path = os.path.join(location, "config.yaml")
    with open(config_path) as f:
        app_config = yaml.load(f, Loader=SafeLoader)
    return app_config

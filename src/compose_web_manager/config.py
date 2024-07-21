"""
@description: Configuration class

@author: Arbuzov Sergey <info@whitediver.com>
"""

import os

import yaml


class Config:
    """Configuration class"""
    def __init__(self, path: str = None):
        self.path = path
        self._config = self._read_config()

    def _read_config(self):
        if self.path is None:
            self.path = os.getenv(
              "COMPOSE_MANAGER_CONFIG_PATH",
              "/etc/compose-web-manager/config.yml"
            )
        with open(self.path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def __getattr__(self, item):
        return os.getenv(item, self._config.get(item))

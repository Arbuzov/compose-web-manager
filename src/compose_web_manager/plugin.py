"""_summary_

Raises:
    ManifestParseException: _description_
    ManifestParseException: _description_
    ManifestParseException: _description_

Returns:
    _type_: _description_
"""
import json
import logging
import os
import tarfile

from .config import Config

config = Config()

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

MANIFEST_FILE = "manifest.json"
COMPOSE_ROOT = config.path.compose
NGINX_SNIPPETS = config.path.nginx


def dict_from_file(file_path):
    """_summary_

    Args:
        file_path (_type_): _description_

    Returns:
        _type_: _description_
    """
    result = {}
    if os.path.exists(file_path):
        with open(file_path, encoding='utf-8') as f:
            for line in f:
                if "=" in line:
                    key, value = line.split("=")
                    result[key] = value.strip()
    return result


class ManifestParseException(Exception):
    """Exception class

    Args:
        Exception (_type_): _description_
    """

    def __init__(self, message):
        super().__init__(message)


class Plugin:
    """Plugin class"""

    def __init__(self, plugin_name):
        self.name = plugin_name

    @staticmethod
    def list_plugins() -> list:
        """
        List all plugins.
        """
        result = []
        if not os.path.exists(COMPOSE_ROOT):
            os.makedirs(COMPOSE_ROOT)
        with os.scandir(COMPOSE_ROOT) as it:
            for entry in it:
                if not entry.name.startswith(".") and entry.is_dir():
                    plugin = Plugin(entry.name)
                    manifest = plugin.get_manifest()
                    if manifest.get("name") == entry.name:
                        result.append(manifest)
        return result

    def mark_dirty(self):
        """
        Mark a plugin as dirty.
        """
        with open(
            f"{COMPOSE_ROOT}/{self.name}/.dirty",
            "w",
            encoding="utf-8"
        ) as f:
            f.write("")

    def mark_clean(self):
        """
        Mark a plugin as clean.
        """
        if os.path.exists(f"{COMPOSE_ROOT}/{self.name}/.dirty"):
            os.remove(f"{COMPOSE_ROOT}/{self.name}/.dirty")

    def restart(self):
        """
        Restart a plugin.
        """
        self.stop()
        self.start()
        self.mark_clean()

    def start(self):
        """
        Start a plugin.
        """
        os.system(
            f"docker compose -f {COMPOSE_ROOT}/{self.name}/docker-compose.yml\
                pull --ignore-pull-failures"
        )
        os.system(
            f"docker compose -f {COMPOSE_ROOT}/{self.name}/docker-compose.yml\
                up -d --remove-orphans"
        )
        self.mark_clean()

    def stop(self):
        """
        Stop a plugin.
        """
        os.system(
            f"docker compose -f {COMPOSE_ROOT}/{self.name}/docker-compose.yml\
                stop"
        )

    def delete(self):
        """
        Delete a plugin.
        """
        self.stop()
        os.system(
            f"docker compose -f {COMPOSE_ROOT}/{self.name}/docker-compose.yml\
                rm --force --stop"
        )
        os.system(f"rm -rf {COMPOSE_ROOT}/{self.name}")

    def get_environment(self):
        """
        Get the environment variables for a plugin.
        """
        result = {}
        env_path = f"{COMPOSE_ROOT}/{self.name}/.env"
        if os.path.exists(env_path):
            result = dict_from_file(env_path)
        return result

    def set_environment_variable(self, name, value):
        """
        Set an environment variable for a plugin.
        """
        env_path = f"{COMPOSE_ROOT}/{self.name}/.env"
        if not os.path.exists(env_path):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("")
                f.close()
        if os.path.exists(env_path):
            env_vars = dict_from_file(env_path)
            env_vars[name] = value
            with open(env_path, "w", encoding="utf-8") as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
        self.mark_dirty()

    def get_info(self):
        """
        Get the information for a plugin.
        """
        result = {
            "compose": "",
            "environment": {},
            "readme": "",
            "manifest": {},
            "dirty": False,
        }
        compose_path = f"{COMPOSE_ROOT}/{self.name}/docker-compose.yml"
        readme_path = f"{COMPOSE_ROOT}/{self.name}/README.md"
        manifest_path = f"{COMPOSE_ROOT}/{self.name}/manifest.json"
        if os.path.exists(compose_path):
            with open(compose_path, encoding="utf-8") as f:
                result["compose"] = f.read()
        result["environment"] = self.get_environment()
        if os.path.exists(readme_path):
            with open(readme_path, encoding='utf-8') as f:
                result["readme"] = f.read()
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as f:
                result["manifest"] = json.load(f)
        if os.path.exists(f"{COMPOSE_ROOT}/{self.name}/.dirty"):
            result["dirty"] = True
        return result

    def get_manifest(self):
        """
        Get the manifest for a plugin.
        """
        manifest_path = f"{COMPOSE_ROOT}/{self.name}/manifest.json"
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding='utf-8') as f:
                return json.load(f)
        return {"name": self.name}

    def has_logo(self):
        """
        Check if a plugin has a logo.
        """
        return os.path.exists(f"{COMPOSE_ROOT}/{self.name}/logo.png")

    def get_logo_path(self):
        """
        Get the path to the logo for a plugin.
        """
        return f"{COMPOSE_ROOT}/{self.name}/logo.png"

    def load_images(self):
        """
        Load images from images/*.tar files if exists
        """
        if os.path.exists(f"{COMPOSE_ROOT}/{self.name}/images"):
            for image in os.listdir(f"{COMPOSE_ROOT}/{self.name}/images"):
                _LOGGER.debug("Loading image %s", image)
                os.system(
                    "docker load -i "
                    + f"{COMPOSE_ROOT}/{self.name}/images/{image}"
                )

    def exists(self):
        """
        Check if a plugin exists.
        """
        return os.path.exists(f"{COMPOSE_ROOT}/{self.name}")

    @staticmethod
    def load_plugin(file_name, apply_environment):
        """
        Args:
            file_name (_type_): _description_
            apply_environment (_type_): _description_

        Raises:
            ManifestParseException: _description_
            ManifestParseException: _description_
            ManifestParseException: _description_

        Returns:
            _type_: _description_
        """
        file = tarfile.open(file_name)
        manifest = {}
        if MANIFEST_FILE not in file.getnames():
            raise ManifestParseException(f"Missing {MANIFEST_FILE}")
        else:
            file.extract(MANIFEST_FILE, "/tmp")
            with open(
                os.path.join("/tmp", MANIFEST_FILE),
                encoding='utf-8'
            ) as f:
                manifest = json.load(f)
                _LOGGER.debug("Manifest: %s", manifest)
        if "name" not in manifest:
            raise ManifestParseException("Missing name in manifest")
        if "version" not in manifest:
            raise ManifestParseException("Missing version in manifest")
        plugin = Plugin(manifest["name"])
        environment = {}
        _LOGGER.debug(
            "exists: %s apply %s",
            plugin.exists(),
            apply_environment
        )
        if plugin.exists() and not apply_environment:
            environment = plugin.get_environment()
        file.extractall(path=os.path.join(COMPOSE_ROOT, manifest["name"]))
        file.close()
        if not apply_environment:
            for key, value in environment.items():
                plugin.set_environment_variable(key, value)
        if os.path.exists(
            os.path.join(COMPOSE_ROOT, manifest["name"], "nginx")
        ):
            if not os.path.exists(NGINX_SNIPPETS):
                os.makedirs(NGINX_SNIPPETS)
            os.system(
                'cp -rf '
                + os.path.join(COMPOSE_ROOT, manifest["name"], "nginx")
                + '/* '
                + NGINX_SNIPPETS
            )
        plugin.load_images()
        plugin.mark_dirty()
        return manifest

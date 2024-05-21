import json
import os
import logging
import tarfile

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

MANIFEST_FILE = 'manifest.json'
SB_COMPOSE_ROOT = '/usr/share/spacebridge/docker'

def dict_from_file(file_path):
  result = {}
  if os.path.exists(file_path):
    with open(file_path) as f:
      for line in f:
        if '=' in line:
            key, value = line.split('=')
            result[key] = value.strip()
  return result

class ManifestParseException(Exception):
    pass

class Plugin:
  
  def __init__(self, plugin_name):
    self.name = plugin_name
    
  @staticmethod
  def list_plugins() -> list:
    """
    List all plugins.
    """
    result = []
    with os.scandir(SB_COMPOSE_ROOT) as it:
      for entry in it:
        if not entry.name.startswith('.') and entry.is_dir():
          plugin = Plugin(entry.name)
          manifest = plugin.get_manifest()
          if (manifest.name == entry.name):
            result.append(manifest)
    return result
    
  def mark_dirty(self):
      """
      Mark a plugin as dirty.
      """
      with open(f'{SB_COMPOSE_ROOT}/{self.name}/.dirty', 'w') as f:
          f.write('')
          
  def mark_clean(self):
      """
      Mark a plugin as clean.
      """
      if os.path.exists(f'{SB_COMPOSE_ROOT}/{self.name}/.dirty'):
        os.remove(f'{SB_COMPOSE_ROOT}/{self.name}/.dirty')
      
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
      os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml pull --ignore-pull-failures')
      os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml up -d --remove-orphans')
      self.mark_clean()
  
  def stop(self):
      """
      Stop a plugin.
      """
      os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml stop')
  
  def delete(self):
      """
      Delete a plugin.
      """
      self.stop
      os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml rm --force --stop')
      os.system(f'rm -rf {SB_COMPOSE_ROOT}/{self.name}')
      
  def get_environment(self):
      """
      Get the environment variables for a plugin.
      """
      result = {}
      env_path = f'{SB_COMPOSE_ROOT}/{self.name}/.env'
      if os.path.exists(env_path):
          with open(env_path) as f:
              result = dict_from_file(env_path)
      return result
  
  def set_environment_variable(self, name, value):
        """
        Set an environment variable for a plugin.
        """
        env_path = f'{SB_COMPOSE_ROOT}/{self.name}/.env'
        if not os.path.exists(env_path):
            with open(env_path, 'w') as f:
                f.write('')
                f.close()
        if os.path.exists(env_path):
            env_vars = dict_from_file(env_path)
            env_vars[name] = value
            with open(env_path, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f'{key}={value}\n')
        self.mark_dirty()
    
  def get_info(self):
      """
      Get the information for a plugin.
      """
      result = {
          'compose': '',
          'environment': {},
          'readme': '',
          'manifest': {},
          'dirty': False
      }
      compose_path = f'{SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml'
      readme_path = f'{SB_COMPOSE_ROOT}/{self.name}/README.md'
      manifest_path = f'{SB_COMPOSE_ROOT}/{self.name}/manifest.json'
      if os.path.exists(compose_path):
          with open(compose_path) as f:
              result['compose'] = f.read()
      result['environment'] = self.get_environment()
      if os.path.exists(readme_path):
          with open(readme_path) as f:
              result['readme'] = f.read() 
      if os.path.exists(manifest_path):
          with open(manifest_path) as f:
              result['manifest'] = json.load(f)
      if os.path.exists(f'{SB_COMPOSE_ROOT}/{self.name}/.dirty'):
          result['dirty'] = True
      return result
  
  def get_manifest(self):
        """
        Get the manifest for a plugin.
        """
        manifest_path = f'{SB_COMPOSE_ROOT}/{self.name}/manifest.json'
        if os.path.exists(manifest_path):
            with open(manifest_path) as f:
                return json.load(f)
        return {"name": self.name}

  def has_logo(self):
      """
      Check if a plugin has a logo.
      """
      return os.path.exists(f'{SB_COMPOSE_ROOT}/{self.name}/logo.png')
  
  def get_logo_path(self):
      """
      Get the path to the logo for a plugin.
      """
      return f'{SB_COMPOSE_ROOT}/{self.name}/logo.png'
      
  def load_images(self):
      """
      Load images from images/*.tar files if exists
      """
      if os.path.exists(f'{SB_COMPOSE_ROOT}/{self.name}/images'):
        for image in os.listdir(f'{SB_COMPOSE_ROOT}/{self.name}/images'):
            _LOGGER.debug(f'Loading image {image}')
            os.system(f'docker load -i {SB_COMPOSE_ROOT}/{self.name}/images/{image}')
            
  def exists(self):
      """
      Check if a plugin exists.
      """
      return os.path.exists(f'{SB_COMPOSE_ROOT}/{self.name}')
    
  @staticmethod
  def load_plugin(file_name, apply_environment):
    file = tarfile.open(file_name)
    manifest = {}
    if MANIFEST_FILE not in file.getnames():
        raise ManifestParseException(f'Missing {MANIFEST_FILE}')
    else:
        file.extract(MANIFEST_FILE,'/tmp')
        with open(os.path.join('/tmp', MANIFEST_FILE)) as f:
            manifest = json.load(f)
            _LOGGER.debug(f'Manifest: {manifest}')
    if 'name' not in manifest:
        raise ManifestParseException('Missing name in manifest')
    if 'version' not in manifest:
        raise ManifestParseException('Missing version in manifest')
    plugin = Plugin(manifest['name'])
    environment = {}
    _LOGGER.debug(f'exists: {plugin.exists()} apply {apply_environment}')
    if plugin.exists() and not apply_environment:
        environment = plugin.get_environment()
    file.extractall(
        path=os.path.join(SB_COMPOSE_ROOT, manifest['name'])
    )
    file.close()
    if not apply_environment:
        for key, value in environment.items():
            plugin.set_environment_variable(key, value)
    
    plugin.load_images()
    plugin.mark_dirty()
    return manifest
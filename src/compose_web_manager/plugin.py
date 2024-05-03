import json
import os
import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

SB_COMPOSE_ROOT = '/usr/share/spacebridge/docker'

def dict_from_file(file_path):
  result = {}
  if os.path.exists(file_path):
    with open(file_path) as f:
      for line in f:
        key, value = line.split('=')
        result[key] = value.strip()
  return result

class Plugin:
  
  def __init__(self, plugin_name):
    self.name = plugin_name
    
  @staticmethod
  def list_plugins():
    """
    List all plugins.
    """
    result = []
    with os.scandir(SB_COMPOSE_ROOT) as it:
      for entry in it:
        if not entry.name.startswith('.') and entry.is_dir():
          result.append(entry.name)
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
      os.system(f'docker compose stop -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml')
      os.system(f'docker compose up -d -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml')
      self.mark_clean()
      
  def start(self):
      """
      Start a plugin.
      """
      os.system(f'docker compose pull {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml')
      os.system(f'docker compose up -d --force-recreate {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml')
      self.mark_clean()
  
  def stop(self):
      """
      Stop a plugin.
      """
      os.system(f'docker compose stop -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml')
  
  def delete(self):
      """
      Delete a plugin.
      """
      os.system(f'docker compose stop -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml')
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
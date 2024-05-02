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
      os.remove(f'{SB_COMPOSE_ROOT}/{self.name}/.dirty')
      
  def restart(self):
      """
      Restart a plugin.
      """
      os.system(f'docker-compose -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml down')
      os.system(f'docker-compose -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml up -d')
      self.mark_clean()
      
  def start(self):
      """
      Start a plugin.
      """
      os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{plugin}/docker-compose.yml pull')
      os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{plugin}/docker-compose.yml up -d --force-recreate')
      self.mark_clean()
  
  def stop(self):
      """
      Stop a plugin.
      """
      os.system(f'docker-compose -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml down')
  
  def delete(self):
      """
      Delete a plugin.
      """
      os.system(f'docker-compose -f {SB_COMPOSE_ROOT}/{self.name}/docker-compose.yml down')
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
      
  def load_images(self):
      """
      Load images from images/*.tar files if exists
      """
      if os.path.exists(f'{SB_COMPOSE_ROOT}/{self.name}/images'):
        for image in os.listdir(f'{SB_COMPOSE_ROOT}/{self.name}/images'):
            _LOGGER.debug(f'Loading image {image}')
            os.system(f'docker load -i {SB_COMPOSE_ROOT}/{self.name}/images/{image}')
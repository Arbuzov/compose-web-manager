import json
import logging
import os
import tarfile
from aiohttp import web

from compose_web_manager.plugin import Plugin, dict_from_file
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

SB_COMPOSE_ROOT = '/usr/share/spacebridge/docker'
SB_REPO_LIST = '/usr/share/spacebridge/docker/repo_list.json'
NGIX_SNIPPETS_PATH = '/etc/nginx/snippets'
MANIFEST_FILE = 'manifest.json'

def list_plugins(request):
  result=[]
  with os.scandir(SB_COMPOSE_ROOT) as it:
    for entry in it:
        if not entry.name.startswith('.') and entry.is_dir():
            result.append(entry.name)
  return web.json_response(result)

async def add_plugin(request):
  data = await request.post()
  plugin = data['plugin']
  
  filename = plugin.filename
  update = open(os.path.join('/tmp', filename), 'wb')
  update.write(plugin.file.read())
  update.close()
  
  file = tarfile.open(os.path.join('/tmp', filename))
  manifest = {}
  if MANIFEST_FILE not in file.getnames():
    return web.json_response({'status': 'error', 'message': f'Missing {MANIFEST_FILE}'})
  else:
    file.extract(MANIFEST_FILE,'/tmp')
    with open(os.path.join('/tmp', MANIFEST_FILE)) as f:
      manifest = json.load(f)
      _LOGGER.debug(f'Manifest: {manifest}')
  if 'name' not in manifest:
    return web.json_response({'status': 'error', 'message': 'Missing name in manifest'})
  if 'version' not in manifest:
    return web.json_response({'status': 'error', 'message': 'Missing version in manifest'})
  
  file.extractall(os.path.join(SB_COMPOSE_ROOT, manifest['name']))
  file.close()
  
  plugin = Plugin(manifest['name'])
  plugin.load_images()
  plugin.mark_dirty()
  return web.json_response({'status': 'ok'})

def get_plugin(request):
  result={
    'compose': '',
    'environment': {},
    'readme': '',
    'manifest': {},
    'dirty': False
  }
  plugin = request.match_info['plugin']
  compose_path = f'{SB_COMPOSE_ROOT}/{plugin}/docker-compose.yml'
  env_path = f'{SB_COMPOSE_ROOT}/{plugin}/.env'
  readme_path = f'{SB_COMPOSE_ROOT}/{plugin}/README.md'
  manifest_path = f'{SB_COMPOSE_ROOT}/{plugin}/manifest.json'
  if os.path.exists(compose_path):
    with open(compose_path) as f:
      result['compose'] = f.read()
  result['environment'] = dict_from_file(env_path)
  if os.path.exists(readme_path):
    with open(readme_path) as f:
      result['readme'] = f.read()
  if os.path.exists(manifest_path):
    with open(manifest_path) as f:
      result['manifest'] = json.load(f)
  if os.path.exists(f'{SB_COMPOSE_ROOT}/{plugin}/.dirty'):
    result['dirty'] = True
  return web.json_response(result)

def start_plugin(request):
  plugin = Plugin(request.match_info['plugin'])
  plugin.start()
  return web.json_response({'status': 'ok'})

def stop_plugin(request):
  plugin = Plugin(request.match_info['plugin'])
  plugin.stop()
  return web.json_response({'status': 'ok'})

def restart_plugin(request):
  plugin = Plugin(request.match_info['plugin'])
  plugin.restart()
  return web.json_response({'status': 'ok'})

def delete_plugin(request):
  plugin = Plugin(request.match_info['plugin'])
  plugin.delete()
  return web.json_response({'status': 'ok'})

def get_plugin_environment(request):
  plugin = Plugin(request.match_info['plugin'])
  result = plugin.get_environment()
  return web.json_response(result)

def get_plugin_variable(request):
  plugin = Plugin(request.match_info['plugin'])
  result = plugin.get_environment().get(request.match_info['name'], '')
  return web.json_response(result)

async def set_plugin_variable(request):
  plugin_name = request.match_info['plugin']
  name = request.match_info['name']
  data = await request.text()
  _LOGGER.debug(f'Setting {name} to {data}')
  env_path = f'{SB_COMPOSE_ROOT}/{plugin_name}/.env'
  if not os.path.exists(env_path):
    with open(env_path, 'w') as f:
      f.write('')
      f.close()
  if os.path.exists(env_path):
    env_vars = dict_from_file(env_path)
    env_vars[name] = data
    with open(env_path, 'w') as f:
      for key, value in env_vars.items():
        f.write(f'{key}={value}\n')
  plugin = Plugin(request.match_info['plugin'])
  plugin.mark_dirty()
  return web.json_response({'status': 'ok'})

def get_repo_list(request):
  result=[]
  if os.path.exists(SB_REPO_LIST):
    with open(SB_REPO_LIST) as f:
      result = json.load(f)
  return web.json_response(result)

async def add_repo(request):
  data = await request.text()
  _LOGGER.debug(f'Adding repo {data}')
  if os.path.exists(SB_REPO_LIST):
    with open(SB_REPO_LIST, 'a') as f:
      f.write(f'{data}\n')
  return web.json_response({'status': 'ok'})

routes = [
  ('GET', '/api/plugins', list_plugins),
  ('POST', '/api/plugins', add_plugin),
  ('GET', r'/api/plugins/{plugin:(\w|\-)*}', get_plugin),
  ('POST', r'/api/plugins/{plugin:(\w|\-)*}/start', start_plugin),
  ('POST', r'/api/plugins/{plugin:(\w|\-)*}/stop', stop_plugin),
  ('POST', r'/api/plugins/{plugin:(\w|\-)*}/restart', restart_plugin),
  ('DELETE', r'/api/plugins/{plugin:(\w|\-)*}', delete_plugin),
  ('GET', r'/api/plugins/{plugin:(\w|\-)*}/environment', get_plugin_environment),
  ('GET', r'/api/plugins/{plugin:(\w|\-)*}/environment/{name:(\w|\-)*}', get_plugin_variable),
  ('POST', r'/api/plugins/{plugin:(\w|\-)*}/environment/{name:(\w|\-)*}', set_plugin_variable),
  ('GET', '/api/repo_list', get_repo_list),
  ('POST', '/api/repo_list', add_repo),
]

import json
import logging
import os
from aiohttp import web
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

SB_COMPOSE_ROOT = '/usr/share/spacebridge/docker'
SB_REPO_LIST = '/usr/share/spacebridge/docker/repo_list.json'

def dict_from_file(file_path):
  result = {}
  if os.path.exists(file_path):
    with open(file_path) as f:
      for line in f:
        key, value = line.split('=')
        result[key] = value.strip()
  return result

def list_plugins(request):
  result=[]
  with os.scandir(SB_COMPOSE_ROOT) as it:
    for entry in it:
        if not entry.name.startswith('.') and entry.is_dir():
            result.append(entry.name)
  return web.json_response(result)

def get_plugin(request):
  result={
    'compose': '',
    'environment': {},
    'readme': '',
    'manifest': {}
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
  return web.json_response(result)

def start_plugin(request):
  plugin = request.match_info['plugin']
  os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{plugin}/docker-compose.yml pull')
  os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{plugin}/docker-compose.yml up -d --force-recreate')
  return web.json_response({'status': 'ok'})

def stop_plugin(request):
  plugin = request.match_info['plugin']
  os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{plugin}/docker-compose.yml down')
  return web.json_response({'status': 'ok'})

def restart_plugin(request):
  plugin = request.match_info['plugin']
  os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{plugin}/docker-compose.yml restart')
  return web.json_response({'status': 'ok'})

def delete_plugin(request):
  plugin = request.match_info['plugin']
  os.system(f'docker compose -f {SB_COMPOSE_ROOT}/{plugin}/docker-compose.yml down')
  os.system(f'rm -rf {SB_COMPOSE_ROOT}/{plugin}')
  return web.json_response({'status': 'ok'})

def get_plugin_environment(request):
  result={}
  plugin = request.match_info['plugin']
  env_path = f'{SB_COMPOSE_ROOT}/{plugin}/.env'
  if os.path.exists(env_path):
    result = dict_from_file(env_path)
  return web.json_response(result)

def get_plugin_variable(request):
  result=''
  plugin = request.match_info['plugin']
  name = request.match_info['name']
  env_path = f'{SB_COMPOSE_ROOT}/{plugin}/.env'
  if os.path.exists(env_path):
    with open(env_path) as f:
      for line in f:
        key, value = line.split('=')
        if key == name:
          result = value.strip()
  return web.json_response(result)

async def set_plugin_variable(request):
  plugin = request.match_info['plugin']
  name = request.match_info['name']
  data = await request.text()
  logging.debug(f'Setting {name} to {data}')
  env_path = f'{SB_COMPOSE_ROOT}/{plugin}/.env'
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
  return web.json_response({'status': 'ok'})

def get_repo_list(request):
  result=[]
  if os.path.exists(SB_REPO_LIST):
    with open(SB_REPO_LIST) as f:
      result = json.load(f)
  return web.json_response(result)

async def add_repo(request):
  data = await request.text()
  logging.debug(f'Adding repo {data}')
  if os.path.exists(SB_REPO_LIST):
    with open(SB_REPO_LIST, 'a') as f:
      f.write(f'{data}\n')
  return web.json_response({'status': 'ok'})

routes = [
  ('GET', '/api/plugins', list_plugins),
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

import json
import logging
import os
from aiohttp import web

from compose_web_manager.plugin import ManifestParseException, Plugin, SB_COMPOSE_ROOT
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

SB_REPO_LIST = '/usr/share/spacebridge/docker/repo_list.json'
NGIX_SNIPPETS_PATH = '/etc/nginx/snippets'
MANIFEST_FILE = 'manifest.json'

def list_plugins(request):
  result=Plugin.list_plugins()
  return web.json_response(result)

async def add_plugin(request):
  data = await request.post()
  plugin = data['plugin']
  apply_environment = data['applyEnvironment'] in ("True", "true", True)
  
  filename = plugin.filename
  update = open(os.path.join('/tmp', filename), 'wb')
  update.write(plugin.file.read())
  update.close()
  
  manifest = {}
  try:
    manifest = Plugin.load_plugin(os.path.join('/tmp', filename), apply_environment)
  except ManifestParseException as e:
    return web.json_response({'status': 'error', 'message': e.message})
  return web.json_response({'status': 'ok', 'manifest': manifest})

def get_plugin(request):
  plugin = Plugin(request.match_info['plugin'])
  result = plugin.get_info()
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
  plugin = Plugin(request.match_info['plugin'])
  name = request.match_info['name']
  data = await request.text()
  _LOGGER.debug(f'Setting {name} to {data}')
  plugin.set_environment_variable(name, data)
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

def logo(request):
  plugin = Plugin(request.match_info['plugin'])
  if not plugin.has_logo():
    return web.Response(status=404)
  return web.FileResponse(plugin.get_logo_path())

routes = [
  ('GET', '/api/plugins', list_plugins),
  ('POST', '/api/plugins', add_plugin),
  ('GET', r'/api/plugins/{plugin:(\w|\-)*}', get_plugin),
  ('POST', r'/api/plugins/{plugin:(\w|\-)*}/start', start_plugin),
  ('GET', r'/api/plugins/{plugin:(\w|\-)*}/logo', logo),
  ('POST', r'/api/plugins/{plugin:(\w|\-)*}/stop', stop_plugin),
  ('POST', r'/api/plugins/{plugin:(\w|\-)*}/restart', restart_plugin),
  ('DELETE', r'/api/plugins/{plugin:(\w|\-)*}', delete_plugin),
  ('GET', r'/api/plugins/{plugin:(\w|\-)*}/environment', get_plugin_environment),
  ('GET', r'/api/plugins/{plugin:(\w|\-)*}/environment/{name:(\w|\-)*}', get_plugin_variable),
  ('POST', r'/api/plugins/{plugin:(\w|\-)*}/environment/{name:(\w|\-)*}', set_plugin_variable),
  ('GET', '/api/repo_list', get_repo_list),
  ('POST', '/api/repo_list', add_repo),
]

import json
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import getcwd, path

HOSTNAME = 'localhost'
PORT = 8080

def MakeRadioRequestHandler(radio_instance):
  class RadioRequestHandler(BaseHTTPRequestHandler):
    radio = radio_instance
    def do_GET(self):
      response = 'Command not supported'
      try:
        command, *args = self.path.lstrip('/').split('/', 1)
        args = None if not args else args[0]
        if command == 'play':
          if args:
             self.radio.play('/'.join(url))
             response = f'Playing radio from {url}'
          else:
            self.radio.play()
            response = f'Resuming with last played url'
        elif command == 'stop':
            self.radio.stop()
            response = f'Stopping playback'
        elif command in ('fav', 'favorite'):
          index, *url = args.split('/', 1)
          url = None if not url else url[0]
          if url:
            self.radio.set_favorite(index, url)
            response = f'Set favorite \'{index}\' to \'{url}\''
          else:
            self.radio.play_favorite(index)
            response = f'Playing favorite \'{index}\''
      except Exception as e:
        response += '\n' + str(e)
      self.send_response(200)
      self.send_header('Content-Type', 'text/plain')
      self.end_headers()
      self.wfile.write(bytes(response, 'utf-8'))
  return RadioRequestHandler


class Radio():
  command = 'exec ffplay -nodisp -nostats -loglevel 8'
  config = { 'playing': None, 'favorites': { } }
  config_path = path.join(getcwd(), 'radio.json')
  process = None

  def __init__(self, config_path:str=None, auto_resume:bool=True):
    if config_path:
      self.config_path = config_path
    self.get_config()
    if auto_resume and 'playing' in self.config and self.config['playing']:
      self.play(self.config['playing'])

  def get_config(self):
    if not path.exists(self.config_path):
      return self.set_config()
    with open(self.config_path, 'r') as f:
      self.config = json.load(f)

  def set_config(self):
    with open(self.config_path, 'w') as f:
      json.dump(self.config, f)

  def play(self, url:str=None):
    if self.process:
      self.stop()
    url = self.config['playing'] if not url else url
    if not url:
      return
    self.process = subprocess.Popen(f'{self.command} {url}', shell=True)
    self.config['playing'] = url
    self.set_config()

  def stop(self):
    if self.process:
      self.process.kill()
      self.process = None

  def set_favorite(self, index, url):
    if not index or not url:
      return
    self.config['favorites'][str(index)] = url
    self.set_config()

  def play_favorite(self, index):
    try:
      url = self.config['favorites'][str(index)]
    except KeyError:
      return
    self.play(url)

if __name__ == '__main__':
  request_handler = MakeRadioRequestHandler(Radio(auto_resume=False))
  server = HTTPServer((HOSTNAME, PORT), request_handler)
  print(f'Server started at http://{HOSTNAME}:{PORT}')

  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass

  server.server_close()
  print('Stopped server')

  # while True:
  #   url = 'http://av.rasset.ie/av/live/radio/radio1.m3u'
  #   radio = Radio()
  #   time.sleep(60)
  #   radio.play(url)
  #   time.sleep(5)
  #   radio.stop()
  #   time.sleep(5)

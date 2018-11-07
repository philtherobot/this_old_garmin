import http.server as _hs
import urllib.parse as _uparse
import subprocess as _subp
import threading as _threading
import requests as _rq
import os as _os
import os.path as _path
import configparser as _configp
import time as _time


this_old_garmin_id = 29665
this_old_garmin_secret='7832770c9dc5dd82b131746a436120470c4d35a2'
this_old_garmin_redirect_uri = 'http://localhost:8000'
browser_path = r'"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"'


def trace(t):
	print('TRACE: {}'.format(t))


def message(t):
	print(t)


def parse_parameters(url):
	parsed = _uparse.urlparse(url)
	return _uparse.parse_qs(parsed.query)	


## Do not access while the server is running.
server_keeps_running = True
authorization_code = ''


class RequestHandler (_hs.BaseHTTPRequestHandler) :
	def do_GET(self):
		self._generic_response()
		trace('received response from authorizer')
		params = parse_parameters(self.requestline)
		if 'code' in params:
			global authorization_code
			authorization_code = params['code'][0]
			trace('code is {}'.format(authorization_code))
			global server_keeps_running
		else:
			trace('no code in response')
		server_keeps_running = False

	def log_request(self, code='-', size='-'):
		pass

	def _generic_response(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		self.wfile.write(bytes('<html><body><h1>This Old Garmin</h1></body></html>', 'utf-8'))


def run_server():
    server_address = ('', 8000)
    httpd = _hs.HTTPServer(server_address, RequestHandler)
    trace('server is starting...')
    global server_keeps_running
    while server_keeps_running:
    	httpd.handle_request()
    trace('server has stopped')


def launch_server():
	server_thread = _threading.Thread(group=None, target=run_server)
	server_thread.start()
	return server_thread


def auth_uri():
	page = 'https://www.strava.com/oauth/authorize'
	parameters = [
		('client_id', this_old_garmin_id),
		('response_type', 'code'),
		('redirect_uri', this_old_garmin_redirect_uri),
		('approval_prompt', 'auto'),
		('scope', 'activity:write')
	]

	params_assign = ['{}={}'.format(k,v) for (k,v) in parameters]

	return page + '?' + '&'.join(params_assign)


def get_authorization_code_request():
	trace('getting authorization code from server')
	server_thread = launch_server();

	_subp.call('{} {}'.format(browser_path, auth_uri()))

	server_thread.join()

	global authorization_code
	trace('got authorization code from server')
	return authorization_code


def get_tokens_request(code):
	trace('get tokens for the first time from the server')
	page = 'https://www.strava.com/oauth/token'
	params = {
		'client_id': this_old_garmin_id,
		'client_secret': this_old_garmin_secret,
		'code': code,
		'grant_type': 'authorization_code'
	}

	r = _rq.post(page, params=params)	
	j = r.json()

	return (
		j['refresh_token'], 
		j['access_token'],
		str(j['expires_at'])
	)


def refresh_tokens_request(refresh_token):
	trace('refresh tokens from the server')
	page = 'https://www.strava.com/oauth/token'
	params = {
		'client_id': this_old_garmin_id,
		'client_secret': this_old_garmin_secret,
		'refresh_token': refresh_token,
		'grant_type': 'refresh_token'
	}

	r = _rq.post(page, params=params)	
	j = r.json()

	return (
		j['refresh_token'], 
		j['access_token'],
		str(j['expires_at'])
	)


def app_data_filename():
	home = _os.getenv('APPDATA')
	return _path.join(home, 'this_old_garmin')


def read_app_data():
	app_data = _configp.ConfigParser()
	try:
		app_data.read(app_data_filename())
	except FileNotFoundError:
		trace('application data file not found')
	return app_data


def write_app_data(app_data):
	with open(app_data_filename(), 'w') as f:
		app_data.write(f)


def is_access_token_valid(ac, ex):

	try:
		expires_at_epoch = float(ex)
		now_epoch = _time.time()
		too_close = 5 * 60 # five minutes

		if now_epoch + too_close > expires_at_epoch:
			return False
	except ValueError:
		return False

	return ac != ''


def is_refresh_token_valid(rf):
	return rf != ''


def is_code_valid(co):
	return co != ''


def update_tokens(section, tokens):
	section['refresh_token'] = tokens[0]
	section['access_token'] = tokens[1]
	section['expires_at'] = tokens[2]


def prepare_access_token(section):
	access_token = section.get('access_token', '')	
	expires_at = section.get('expires_at', '')	

	if not is_access_token_valid(access_token, expires_at):
		get_access_token(section)

	trace('access token is {}'.format(section['access_token']))


def get_access_token(section):
	# access token is invalid or expired
	refresh_token = section.get('refresh_token', '')

	if is_refresh_token_valid(refresh_token):
		tokens = refresh_tokens_request(refresh_token)
		update_tokens(section, tokens)
	else:
		get_tokens_from_authorization_code(section)


def get_tokens_from_authorization_code(section):
	# refresh and access tokens are invalid
	code = section.get('code', '')

	if not is_code_valid(code):
		code = get_authorization_code_request()
		section['code'] = code

	tokens = get_tokens_request(code)

	update_tokens(section, tokens)


def get_section(configp, name):
	try:
		return configp[name]
	except KeyError:
		configp.add_section(name)
		return configp[name]


def main():
	app_data = read_app_data()

	authorization_section = get_section(app_data, 'authorization')

	prepare_access_token(authorization_section)

	write_app_data(app_data)

	# TODO get data from Garmin unit
	# TODO push data to site with access token

if __name__ == "__main__": 
	main()

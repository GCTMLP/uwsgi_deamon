import os
import re
import json
import requests
import logging


OK = 200
BAD_REQUEST = 400
INTERNAL_ERROR = 500
MAX_CONN_TRYING = 5

def get_weather(env):
	code, ip = parse_url(env)
	if code != OK:
		return code, ip
	code, city_country = get_city(ip)
	if code != OK:
		return code, ip
	code, weather = get_weather_data(city_country)
	return code, weather


def parse_url(env):
	ip = env.strip('/').split('/')[-1]
	
	if re.fullmatch(r'\d{1,3}?\.\d{1,3}?\.\d{1,3}?\.\d{1,3}', ip):
		for octet in ip.split('.'):
			if int(octet) < 1 or int(octet) > 255:
				err_msg = "Wrong ip: {}".format(ip)
				return BAD_REQUEST, err_msg
		return OK, ip
	else:
		err_msg = "Wrong ip: {}".format(ip)
		return BAD_REQUEST, err_msg


def get_city(ip, trying=0):
	res = requests.get('https://ipinfo.io/'+ip)
	data = res.json()
	if res.status_code != OK:
		if trying < MAX_CONN_TRYING:
			trying+=1
			get_city(ip, trying)
		else:
			msg = "Error in connecting to ipinfo.io"
			return INTERNAL_ERROR, msg
	elif 'city' not in data.keys() and 'country' not in data.keys():
		msg = "Cannot find country or city by this ip {}".format(ip)
		return BAD_REQUEST, msg
	else:
		return OK, data['city']


def get_weather_data(city, trying=0):
	#app_key = os.environ.get("WEATHER_API_KEY")
	app_key = "e86882e61a7d2d99fedb3986a156824f"
	res = requests.get('https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&lang=ru&appid={}'.format(city, app_key))
	if res.status_code != OK:
		if trying < MAX_CONN_TRYING:
			trying+=1
			get_weather_data(city, trying)
		else:
			msg = "Error in connecting to api.openweathermap.org"
			return INTERNAL_ERROR, msg
	else:
		data = res.json()
		if 'main' in data.keys() and 'weather' in data.keys():
			response = {'city':city,
						'temp':int(data['main']['temp']),
						'conditions':','.join([weather['description'] for weather in data['weather']])}
			return OK, response
		else:
			msg = "Cannot find weather data in {}".format(city)
			return BAD_REQUEST, msg
	


def application(environ, start_response):
	code, response = get_weather(environ['REQUEST_URI'])	
	if not isinstance(response, str):
		response = json.dumps(response, ensure_ascii=False, indent="\t")
	response = response.encode(encoding="UTF-8")
	response_headers = [
		('Content-Type', 'text/plain'),
		('Content-Length', str(len(response)))
	]
	start_response(str(code), response_headers)
	return [response]


print(get_weather_data('fdfdf', 4))
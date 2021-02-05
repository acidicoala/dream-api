import json
import re
from urllib.parse import urlparse, parse_qs
from xml.etree import ElementTree

from mitmproxy.http import HTTPFlow, HTTPResponse

from setup.config import Config
from util.log import Log


class DreamAPIAddon:
	@staticmethod
	def request(flow: HTTPFlow):
		if Config().block_telemetry:
			DreamAPIAddon.block_epic_telemetry(flow)

	@staticmethod
	def response(flow: HTTPFlow):
		DreamAPIAddon.hack_epicgames(flow)
		DreamAPIAddon.hack_origin(flow)

	@staticmethod
	def hack_epicgames(flow: HTTPFlow):
		if DreamAPIAddon.host_and_path_match(
				flow,
				host=r"^api\.epicgames\.dev$",
				path=r"^/epic/ecom/v1/platforms/EPIC/identities/\w+/ownership$"
		):
			Log().info('Intercepted a DLC request from Epic Games')

			url = urlparse(flow.request.url)
			params = parse_qs(url.query)['nsCatalogItemId']

			for param in params:
				Log().info(f"\t{param}")

			# noinspection PyShadowingNames
			result = list(map(lambda param: {
				'namespace': param.split(':')[0],
				'itemId': param.split(':')[1],
				'owned': True
			}, params))

			flow.response.status_code = 200
			flow.response.reason = "OK"
			flow.response.text = json.dumps(result)

			# Remove the error headers, just to be sure
			flow.response.headers.pop('x-epic-error-code')
			flow.response.headers.pop('x-epic-error-name')

	@staticmethod
	def hack_origin(flow: HTTPFlow):
		if DreamAPIAddon.host_and_path_match(
				flow,
				host=r"^api\d*\.origin\.com$",
				path=r"^/ecommerce2/products$"
		):
			Log().info('Intercepted a DLC request from Origin ')

			tree = ElementTree.fromstring(flow.response.text)

			# Make all items owned
			for elem in tree.iter():
				# TODO: Log DLC ids
				if elem.tag == 'isOwned':
					elem.text = 'true'
				elif elem.tag == 'userCanPurchase':
					elem.text = 'false'

			flow.response.status_code = 200
			flow.response.reason = "OK"
			flow.response.text = ElementTree.tostring(tree, encoding='unicode')

	@staticmethod
	def host_and_path_match(flow: HTTPFlow, host: str, path: str):
		req_host = flow.request.pretty_host
		req_path = urlparse(flow.request.url).path

		return re.match(host, req_host) and re.match(path, req_path)

	@staticmethod
	def block_epic_telemetry(flow: HTTPFlow):
		if flow.request.path.startswith('/telemetry'):
			flow.response = HTTPResponse.make(500, 'No more spying')
			Log().debug('Blocked telemetry request from Epic Games')

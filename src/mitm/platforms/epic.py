import json
from typing import Union, Dict, List
from urllib.parse import urlparse, parse_qs

from mitmproxy.http import HTTPFlow, HTTPResponse

from mitm.platforms.base import BasePlatform
from setup.config import config
from util.log import log


class EpicPlatform(BasePlatform):
	def __init__(self, flow: HTTPFlow):
		super().__init__(flow)

	@staticmethod
	def handle_request(flow: HTTPFlow):
		epic = EpicPlatform(flow)
		epic.block_telemetry()

	@staticmethod
	def handle_response(flow: HTTPFlow):
		epic = EpicPlatform(flow)
		epic.intercept_ownership()
		epic.intercept_entitlements()

	def intercept_ownership(self):
		if self.host_and_path_match(
				host=r"^api\.epicgames\.dev$",
				path=r"^/epic/ecom/v1/platforms/EPIC/identities/\w+/ownership$"
		):
			log.info('Intercepted an Ownership request from Epic Games')

			url = urlparse(self.flow.request.url)
			params = parse_qs(url.query)['nsCatalogItemId']

			[log.debug(f'\t{param}') for param in params]

			result = [{
				'namespace': param.split(':')[0],
				'itemId': param.split(':')[1],
				'owned': True
			} for param in params]

			self.modify_response(result)

	def intercept_entitlements(self):
		if self.host_and_path_match(
				host=r"^ecommerceintegration.+\.epicgames\.com$",
				path=r"^/ecommerceintegration/api/public/v2/identities/\w+/entitlements$"
		):
			log.info('Intercepted an Entitlements request from Epic Games')

			url = urlparse(self.flow.request.url)
			sandbox_id = parse_qs(url.query)['sandboxId'][0]

			try:
				# Get the entitlements from request params
				entitlementNames = parse_qs(url.query)['entitlementName']
			except KeyError:
				log.warning(
						'No entitlement names were provided, '
						'responding with entitlements defined in the config file'
				)

				# Get the game in the config with namespace that matches the sandboxId
				game = next((game for game in config.platforms['epic'] if game['namespace'] == sandbox_id), None)

				# Get the game's entitlements
				entitlements = game['entitlements'] if game is not None else []

				# Map the list of objects to the list of string
				entitlementNames = [entitlement['id'] for entitlement in entitlements]

			result = [{
				'id': entitlementName,  # Not true, but irrelevant
				'entitlementName': entitlementName,
				'namespace': sandbox_id,
				'catalogItemId': entitlementName,
				'entitlementType': "AUDIENCE",
				'grantDate': "2021-01-01T00:00:00.000Z",
				'consumable': False,
				'status': "ACTIVE",
				'useCount': 0,
				'entitlementSource': "eos"
			} for entitlementName in entitlementNames]

			self.modify_response(result)

	def modify_response(self, content: Union[Dict, List]):
		self.flow.response.status_code = 200
		self.flow.response.reason = "OK"
		self.flow.response.text = json.dumps(content)

		# Remove the error headers, if they are present
		try:
			self.flow.response.headers.pop('x-epic-error-code')
			self.flow.response.headers.pop('x-epic-error-name')
		except KeyError:
			pass

	def block_telemetry(self):
		if config.block_telemetry and self.flow.request.path.startswith('/telemetry'):
			self.flow.response = HTTPResponse.make(500, 'No more spying')
			log.debug('Blocked telemetry request from Epic Games')

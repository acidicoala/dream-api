import json
from typing import Union, Dict, List
from urllib.parse import urlparse, parse_qs

from mitmproxy.http import HTTPFlow, HTTPResponse

from mitm.addons.base import BaseAddon
from mitm.addons.base import log_exceptions
from setup.config import config
from util.log import log


class EpicAddon(BaseAddon):
	api_host = r'api\.epicgames\.dev'
	ecom_host = r'ecommerceintegration.+\.epicgames\.com'

	hosts = BaseAddon.get_hosts([
		api_host, ecom_host
	])

	@staticmethod
	@log_exceptions
	def request(flow: HTTPFlow):
		EpicAddon.block_telemetry(flow)

	@staticmethod
	@log_exceptions
	def response(flow: HTTPFlow):
		EpicAddon.intercept_ownership(flow)
		EpicAddon.intercept_entitlements(flow)

	@staticmethod
	def intercept_ownership(flow: HTTPFlow):
		if BaseAddon.host_and_path_match(
				flow,
				host=EpicAddon.api_host,
				path=r"^/epic/ecom/v1/platforms/EPIC/identities/\w+/ownership$"
		):
			log.info('Intercepted an Ownership request from Epic Games')

			url = urlparse(flow.request.url)
			params = parse_qs(url.query)['nsCatalogItemId']

			# Each nsCatalogItemId is formatted as '{namespace}:{item_id}'
			[log.debug(f'\t{param}') for param in params]

			result = [{
				'namespace': param.split(':')[0],
				'itemId': param.split(':')[1],
				'owned': True
			} for param in params]

			EpicAddon.modify_response(flow, result)

	@staticmethod
	def intercept_entitlements(flow: HTTPFlow):
		if BaseAddon.host_and_path_match(
				flow,
				host=EpicAddon.ecom_host,
				path=r"^/ecommerceintegration/api/public/v2/identities/\w+/entitlements$"
		):
			log.info('Intercepted an Entitlements request from Epic Games')

			url = urlparse(flow.request.url)
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

			[log.debug(f'\t{sandbox_id}:{entitlement}') for entitlement in entitlementNames]

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

			EpicAddon.modify_response(flow, result)

	@staticmethod
	def modify_response(flow: HTTPFlow, content: Union[Dict, List]):
		flow.response.status_code = 200
		flow.response.reason = "OK"
		flow.response.text = json.dumps(content)

		# Remove the error headers, if they are present
		try:
			flow.response.headers.pop('x-epic-error-code')
			flow.response.headers.pop('x-epic-error-name')
		except KeyError:
			pass

	@staticmethod
	def block_telemetry(flow: HTTPFlow):
		if config.block_telemetry and flow.request.path.startswith('/telemetry'):
			flow.response = HTTPResponse.make(500, 'No more spying')
			log.debug('Blocked telemetry request from Epic Games')

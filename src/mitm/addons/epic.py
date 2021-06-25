import json
import re
from typing import Union, Dict, List, TypedDict
from urllib.parse import urlparse, parse_qs

from mitmproxy.http import HTTPFlow, HTTPResponse

from mitm.addons.base import BaseAddon
from mitm.addons.base import log_exceptions
from setup.config import config, EpicGame, Entitlement
from util.log import log


def get_epic_game(namespace: str) -> EpicGame:
	return next((game for game in config.platforms['epic'] if game['namespace'] == namespace), None)


def get_epic_blacklist(game: EpicGame) -> List[Entitlement]:
	return [dlc['id'] for dlc in game['blacklist']] if game is not None and 'blacklist' in game else []


class EpicEntitlement(TypedDict):
	catalogItemId: str
	consumable: bool
	entitlementName: str
	entitlementSource: str
	entitlementType: str
	grantDate: str
	id: str
	namespace: str
	status: str
	useCount: int


class EpicAddon(BaseAddon):
	api_host = r'api\.epicgames\.dev'
	ecom_host = r'ecommerceintegration.*\.epicgames\.com'
	library_service_host = r'library-service\.live\..*\.on\.epicgames\.com'

	hosts = BaseAddon.get_hosts([
		api_host, ecom_host, library_service_host
	])

	@staticmethod
	@log_exceptions
	def request(flow: HTTPFlow):
		EpicAddon.block_telemetry(flow)
		EpicAddon.block_playtime(flow)

	@staticmethod
	@log_exceptions
	def response(flow: HTTPFlow):
		# log.debug(f'EpicAddon. Path: {flow.request.path}')
		# EpicAddon.intercept_offers(flow)
		EpicAddon.intercept_ownership(flow)
		EpicAddon.intercept_entitlements(flow)

	@staticmethod
	def intercept_offers(flow: HTTPFlow):
		"""No effect in intercepting this one I suppose"""
		if BaseAddon.host_and_path_match(
				flow,
				host=EpicAddon.api_host,
				path=r"^/epic/ecom/v1/identities/\w+/namespaces/\w+/offers"
				# legacy path: r"^/ecommerceintegration/api/public/eos/identities/.+/namespaces/.+/offers"
		):
			log.info('Intercepted an Offers request from Epic Games')

			response: dict = json.loads(flow.response.text)

			elements: List[dict] = response['elements']
			if elements is not None:
				for element in elements:
					if element['purchasedCount'] == 0:
						element['purchasedCount=0'] = 1

			EpicAddon.modify_response(flow, elements)

	@staticmethod
	def intercept_ownership(flow: HTTPFlow):
		param_string = None

		if BaseAddon.host_and_path_match(
				flow,
				host=EpicAddon.api_host,
				path=r"^/epic/ecom/v1/platforms/EPIC/identities/\w+/ownership$"
		):  # Current endpoint
			param_string = 'nsCatalogItemId'
		elif BaseAddon.host_and_path_match(
				flow,
				host=EpicAddon.ecom_host,
				path=r"^/ecommerceintegration/api/public/platforms/EPIC/identities/\w+/ownership$"
		):  # Legacy endpoint
			param_string = 'nsItemId'

		if param_string is None:
			return

		log.info('Intercepted an Ownership request from Epic Games')

		url = urlparse(flow.request.url)
		params = parse_qs(url.query)[param_string]

		# Each nsCatalogItemId/nsItemId is formatted as '{namespace}:{item_id}'
		[log.debug(f'\t{param}') for param in params]

		def process_game(param: str):
			namespace, itemID = param.split(':')
			game = get_epic_game(namespace)
			owned = True if game is None else itemID not in get_epic_blacklist(game)
			return {
				'namespace': namespace,
				'itemId': itemID,
				'owned': owned,
			}

		result = [process_game(param) for param in params]

		EpicAddon.modify_response(flow, result)

	@staticmethod
	def intercept_entitlements(flow: HTTPFlow):
		if BaseAddon.host_and_path_match(
				flow, host=EpicAddon.ecom_host,
				path=r"^/ecommerceintegration/api/public/v2/identities/\w+/entitlements$"
		) or BaseAddon.host_and_path_match(
				flow, host=EpicAddon.api_host,
				path=r"^/epic/ecom/v1/identities/\w+/entitlements"
		):
			log.info('Intercepted an Entitlements request from Epic Games')

			url = urlparse(flow.request.url)
			sandbox_id = parse_qs(url.query)['sandboxId'][0]

			# Get the game in the config with namespace that matches the sandboxId
			game = get_epic_game(sandbox_id)

			try:
				# Get the entitlements from request params
				entitlementNames = parse_qs(url.query)['entitlementName']
			except KeyError:
				log.warning(
						'No entitlement names were provided, '
						'responding with entitlements defined in the config file'
				)

				# Get the game's entitlements
				entitlements = game['entitlements'] if game is not None and 'entitlements' in game else []

				# Map the list of objects to the list of string
				entitlementNames = [entitlement['id'] for entitlement in entitlements]

			[log.debug(f'\t{sandbox_id}:{entitlement}') for entitlement in entitlementNames]

			# Filter out blacklisted entitlements
			entitlementNames = [e for e in entitlementNames if e not in get_epic_blacklist(game)]

			injected_entitlements: List[EpicEntitlement] = [{
				'id': entitlementName,  # Not true, but irrelevant
				'entitlementName': entitlementName,
				'namespace': sandbox_id,
				'catalogItemId': entitlementName,
				'entitlementType': "AUDIENCE",
				'grantDate': "2021-01-01T00:00:00.000Z",
				'consumable': False,
				'status': "ACTIVE",
				'useCount': 0,
				'entitlementSource': "LauncherWeb"
			} for entitlementName in entitlementNames]

			log.info(f'Injecting {len(injected_entitlements)} entitlements')

			original_entitlements: List[EpicEntitlement] = json.loads(flow.response.text)

			merged_entitlements = original_entitlements + injected_entitlements

			EpicAddon.modify_response(flow, merged_entitlements)

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
			flow.request.text = '{}'  # Just in case

			flow.response = HTTPResponse.make(200, '{}')
			flow.response.headers.add('Content-Type', 'application/json')
			flow.response.headers.add('server', 'eos-gateway')
			flow.response.headers.add('access-control-allow-origin', '*')
			flow.response.headers.add('x-epic-correlation-id', '12345678-1234-1234-1234-123456789abc')

			log.info('Blocked telemetry request from Epic Games')

	@staticmethod
	def block_playtime(flow: HTTPFlow):
		if config.block_playtime and flow.request.path.startswith('/library/api/public/playtime/'):
			original_playtime = json.loads(flow.request.text)
			flow.request.text = '{}'  # Just in case

			correlation_id = flow.request.headers.get('X-Epic-Correlation-ID')
			if m := re.match(r"UE4-(\w+)", correlation_id):
				device_id = m.group(1)
			else:
				device_id = '123456789abcdef01234567890abcdef'

			flow.response = HTTPResponse.make(204)
			flow.response.headers.add('x-epic-device-id', device_id)
			flow.response.headers.add('x-epic-correlation-id', correlation_id)
			flow.response.headers.add('x-envoy-upstream-service-time', '10')  # ?
			flow.response.headers.add('server', 'istio-envoy')

			log.info('Blocked playtime request from Epic Games')
			log.debug(f'\n{json.dumps(original_playtime, indent=4)}')

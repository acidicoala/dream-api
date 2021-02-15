import json
from typing import List, Dict, TypedDict
from xml.etree import ElementTree

import requests
from mitmproxy.http import HTTPFlow, HTTPResponse
from pefile import PE
from pymem import Pymem
from pymem.exception import ProcessNotFound

from mitm.addons.base import BaseAddon, log_exceptions
from setup.config import config
from util.log import log


class OriginEntitlement(TypedDict):
	productId: str
	entitlementTag: str
	groupName: str
	entitlementId: int
	entitlementType: str
	lastModifiedDate: str
	entitlementSource: str
	grantDate: str
	suppressedBy: List
	version: int
	isConsumable: bool
	productCatalog: str
	suppressedOffers: List
	originPermissions: str
	useCount: int
	projectId: str
	status: str


class OriginAddon(BaseAddon):
	last_origin_pid = 0
	injected_entitlements: List[OriginEntitlement] = []
	api_host = r'api\d*\.origin\.com'

	hosts = BaseAddon.get_hosts([
		api_host
	])

	@log_exceptions
	def __init__(self):
		self.fetch_entitlements()
		self.patch_origin_client()

	@staticmethod
	@log_exceptions
	def request(flow: HTTPFlow):
		OriginAddon.block_telemetry(flow)

	@log_exceptions
	def response(self, flow: HTTPFlow):
		self.intercept_entitlements(flow)
		OriginAddon.intercept_products(flow)

	def intercept_entitlements(self, flow: HTTPFlow):
		if BaseAddon.host_and_path_match(
				flow,
				host=OriginAddon.api_host,
				path=r"^/ecommerce2/entitlements/\d+$"
		):  # Real DLC request
			self.patch_origin_client()

			log.info('Intercepted an Entitlements request from Origin ')

			# Get legit user entitlements
			try:
				entitlements: List[OriginEntitlement] = json.loads(flow.response.text)['entitlements']
			except KeyError:
				entitlements = []

			# Inject our entitlements
			entitlements.extend(self.injected_entitlements)

			[log.debug(f"\t{e['entitlementTag']}") for e in entitlements]

			# Modify response
			flow.response.status_code = 200
			flow.response.reason = 'OK'
			flow.response.text = json.dumps({'entitlements': entitlements})

			flow.response.headers.add('X-Origin-CurrentTime', '1609452000')
			flow.response.headers.add('X-Origin-Signature', 'nonce')

	@staticmethod
	def intercept_products(flow: HTTPFlow):
		if BaseAddon.host_and_path_match(
				flow,
				host=OriginAddon.api_host,
				path=r"^/ecommerce2/products$"
		):  # Just for store page, no effect in game
			log.info('Intercepted a Products request from Origin')
			tree = ElementTree.fromstring(flow.response.text)

			for elem in tree.iter():
				if elem.tag == 'offer':
					log.debug(f"\t{elem.attrib['offerId']}")
				elif elem.tag == 'isOwned':
					elem.text = 'true'
				elif elem.tag == 'userCanPurchase':
					elem.text = 'false'

			flow.response.status_code = 200
			flow.response.reason = "OK"
			flow.response.text = ElementTree.tostring(tree, encoding='unicode')

	@staticmethod
	def block_telemetry(flow: HTTPFlow):
		if config.block_telemetry and flow.request.path.startswith('/ratt/telm'):
			flow.response = HTTPResponse.make(500, 'No more spying')
			log.debug('Blocked telemetry request from Origin')

	def fetch_entitlements(self):
		log.debug('Fetching origin entitlements...')

		url = 'https://raw.githubusercontent.com/acidicoala/origin-entitlements/master/sims4.json'
		response = requests.get(url)
		self.injected_entitlements = response.json()

		log.debug('Origin entitlements were successfully fetched')

	# Credit to anadius for the idea
	def patch_origin_client(self):
		PROCESS_NAME = 'Origin.exe'
		DLL_NAME = 'libeay32.dll'
		FUNCTION_NAME = 'EVP_DigestVerifyFinal'

		try:
			origin_process = Pymem(PROCESS_NAME)
		except ProcessNotFound:
			log.warning('Origin process not found. Patching aborted.')
			return

		if origin_process.process_id == self.last_origin_pid:
			# Origin is already patched.
			return

		log.info('Patching Origin client...')

		try:
			libeay32_module = next(m for m in origin_process.list_modules() if m.name.lower() == DLL_NAME)
		except StopIteration:
			log.error(f'{DLL_NAME} is not loaded. Patching aborted.')
			return

		# The rest should complete without issues in most cases.

		# Get the Export Address Table symbols
		# noinspection PyUnresolvedReferences
		libeay32_dll_symbols = PE(libeay32_module.filename).DIRECTORY_ENTRY_EXPORT.symbols

		# Get the symbol of the EVP_DigestVerifyFinal function
		verify_func_symbol = next(s for s in libeay32_dll_symbols if s.name.decode('ascii') == FUNCTION_NAME)

		# Calculate the final address in memory
		verify_func_addr = libeay32_module.lpBaseOfDll + verify_func_symbol.address

		# Instructions to patch. We return 1 to force successful response validation.
		patch_instructions = bytes([
			0xB8, 0x01, 0, 0, 0,  # mov eax, 0x1
			0xC3, 0, 0, 0, 0  # ret
		])
		origin_process.write_bytes(verify_func_addr, patch_instructions, len(patch_instructions))

		# Validate the written memory
		read_instructions = origin_process.read_bytes(verify_func_addr, len(patch_instructions))

		if read_instructions != patch_instructions:
			log.error('Failed to patch the instruction memory. Patching failed.')
			return

		# At this point we know that patching was successful

		self.last_origin_pid = origin_process.process_id
		log.info(f'Patching Origin was successful')

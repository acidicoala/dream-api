import json
import struct
from os.path import isfile
from xml.etree import ElementTree
from collections import namedtuple

import requests
from mitmproxy.http import HTTPResponse
from pefile import PE
from pymem import Pymem
from pymem.exception import ProcessNotFound

from mitm.addons.base import *
from setup.config import config
from util.log import log
from util.resource import get_data_path


def xml2entitlements(xml_string):
	tree = ElementTree.fromstring(xml_string)

	entitlements = []
	for entitlement in tree.findall('entitlement'):
		entitlement_dict = {}
		for element in entitlement:
			entitlement_dict[element.tag] = element.text
		entitlements.append(entitlement_dict)

	return entitlements


def entitlements2xml(entitlements):
	XML_DECLARATION = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
	root = ElementTree.Element('entitlements')

	for ent in entitlements:
		entitlement = ElementTree.SubElement(root, 'entitlement')
		for key, value in ent.items():
			ElementTree.SubElement(entitlement, key).text = str(value)

	return XML_DECLARATION + ElementTree.tostring(root, encoding='utf-8')


Client = namedtuple('Client', 'NAME PROCESS_NAME DLL_NAME FUNCTION_NAME')


class OriginAddon(BaseAddon):
	last_client_pid = 0
	injected_entitlements = []
	api_host = r'api\d*\.origin\.com'
	entitlements_path = get_data_path('origin-entitlements.json')

	hosts = BaseAddon.get_hosts([
		api_host
	])

	@log_exceptions
	def __init__(self):
		self.patch_origin_client()
		self.fetch_entitlements_if_necessary()
		self.read_entitlements_from_cache()

	@staticmethod
	@log_exceptions
	def request(flow: HTTPFlow):
		OriginAddon.block_telemetry(flow)

	@log_exceptions
	def response(self, flow: HTTPFlow):
		self.intercept_entitlements(flow)
		self.intercept_products(flow)

	def intercept_entitlements(self, flow: HTTPFlow):
		if BaseAddon.host_and_path_match(
				flow,
				host=OriginAddon.api_host,
				path=r"^/ecommerce2/entitlements/\d+$"
		):  # Real DLC request
			self.patch_origin_client()

			log.info('Intercepted an Entitlements request from Origin ')

			xml_mode = 'application/xml' in flow.response.headers['content-type']
			# Get legit user entitlements
			if xml_mode:
				entitlements: List = xml2entitlements(flow.response.text)
			else:
				try:
					entitlements: List = json.loads(flow.response.text)['entitlements']
				except KeyError:
					entitlements = []

			# Inject our entitlements
			entitlements.extend(self.injected_entitlements)

			# Filter out blacklisted DLCs
			blacklist = [game['id'] for game in config.platforms['origin']['blacklist']]
			entitlements = [e for e in entitlements if e['entitlementTag'] not in blacklist]

			for e in entitlements:
				try:
					log.debug(f"\t{e['___name']}")
				except KeyError:
					log.debug(f"\t{e['entitlementTag']}")

			# Modify response
			flow.response.status_code = 200
			flow.response.reason = 'OK'
			if xml_mode:
				flow.response.content = entitlements2xml(entitlements)
			else:
				flow.response.text = json.dumps({'entitlements': entitlements})

			flow.response.headers.add('X-Origin-CurrentTime', '1609452000')
			flow.response.headers.add('X-Origin-Signature', 'nonce')

	def intercept_products(self, flow: HTTPFlow):
		if BaseAddon.host_and_path_match(
				flow,
				host=self.api_host,
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

	def fetch_entitlements_if_necessary(self):
		log.debug('Fetching Origin entitlements')

		# Get the etag
		etag_path = get_data_path('origin-entitlements.etag')
		etag = ''
		if isfile(self.entitlements_path) and isfile(etag_path):
			with open(etag_path, mode='r') as file:
				etag = file.read()

		# Fetch entitlements if etag does not match
		url = 'https://raw.githubusercontent.com/acidicoala/public-entitlements/main/origin/v1/entitlements.json'

		try:
			response = requests.get(url, headers={'If-None-Match': etag}, timeout=10)
		except Exception as e:
			log.error(f"Failed to fetch origin entitlements. {str(e)}")
			return

		if response.status_code == 304:
			log.debug(f'Cached Origin entitlements have not changed')
			return

		if response.status_code != 200:
			log.error(f'Error while fetching entitlements: {response.status_code} - {response.text}')
			return

		try:
			index = 1000000
			entitlements: List[dict] = json.loads(response.text)
			for entitlement in entitlements:
				entitlement.update({
					"entitlementId": index,
					"lastModifiedDate": "2020-01-01T00:00Z",
					"entitlementSource": "ORIGIN-OIG",
					"grantDate": "2020-01-01T00:00:00Z",
					"suppressedBy": [],
					"version": 0,
					"isConsumable": False,
					"productCatalog": "OFB",
					"suppressedOffers": [],
					"originPermissions": "0",
					"useCount": 0,
					"projectId": "123456",
					"status": "ACTIVE"
				})
				index += 1
		except ValueError as e:
			log.error(f"Failed to decode entitlements from json. {str(e)}")
			return

		# Cache entitlements
		with open(self.entitlements_path, 'w') as f:
			f.write(json.dumps(entitlements, indent=4, ensure_ascii=False))

		# Cache etag
		with open(etag_path, 'w') as f:
			f.write(response.headers['etag'])

		log.info('Origin entitlements were successfully fetched and cached')

	def read_entitlements_from_cache(self):
		log.debug('Reading origin entitlements from cache')

		with open(self.entitlements_path, mode='r') as file:
			self.injected_entitlements: list = json.loads(file.read())

		log.info(f'{len(self.injected_entitlements)} Origin entitlements were successfully read from cache')

	# Credit to anadius for the idea
	@synchronized_method
	def patch_origin_client(self):
		origin = Client('Origin', 'Origin.exe', 'libeay32.dll', 'EVP_DigestVerifyFinal')
		eadesktop = Client('EA Desktop', 'EADesktop.exe', 'libcrypto-1_1-x64.dll', 'EVP_DigestVerifyFinal')

		client = origin

		try:
			client_process = Pymem(client.PROCESS_NAME)
		except ProcessNotFound:
			client = eadesktop
			try:
				client_process = Pymem(client.PROCESS_NAME)
			except ProcessNotFound:
				log.warning('Origin/EA Desktop process not found. Patching aborted')
				return

		if client_process.process_id == self.last_client_pid:
			log.debug(f'{client.NAME} client is already patched')
			return

		log.info(f'Patching {client.NAME} client')

		try:
			dll_module = next(m for m in client_process.list_modules() if m.name.lower() == client.DLL_NAME)
		except StopIteration:
			log.error(f'{client.DLL_NAME} is not loaded. Patching aborted')
			return

		# The rest should complete without issues in most cases.

		# Get the Export Address Table symbols
		# noinspection PyUnresolvedReferences
		dll_symbols = PE(dll_module.filename).DIRECTORY_ENTRY_EXPORT.symbols

		# Get the symbol of the EVP_DigestVerifyFinal function
		verify_func_symbol = next(s for s in dll_symbols if s.name.decode('ascii') == client.FUNCTION_NAME)

		# Calculate the final address in memory
		verify_func_addr = dll_module.lpBaseOfDll + verify_func_symbol.address

		# Instructions to patch. We return 1 to force successful response validation.
		patch_instructions = bytes([
			0x66, 0xB8, 0x01, 0,  # mov ax, 0x1
			0xC3  # ret
		])
		client_process.write_bytes(verify_func_addr, patch_instructions, len(patch_instructions))

		# Validate the written memory
		read_instructions = client_process.read_bytes(verify_func_addr, len(patch_instructions))

		if read_instructions != patch_instructions:
			log.error('Failed to patch the instruction memory')
			return

		# At this point we know that patching was successful

		self.last_client_pid = client_process.process_id
		log.info(f'Patching {client.NAME} was successful')

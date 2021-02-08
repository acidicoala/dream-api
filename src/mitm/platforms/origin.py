import json
from typing import List, Dict
from xml.etree import ElementTree

from mitmproxy.http import HTTPFlow, HTTPResponse

from mitm.platforms.base import BasePlatform
from setup.config import config
from util.log import log


class OriginPlatform(BasePlatform):
	def __init__(self, flow: HTTPFlow):
		super().__init__(flow)

		self.intercept_entitlements()
		self.intercept_products()

	@staticmethod
	def handle_request(flow: HTTPFlow):
		origin = OriginPlatform(flow)
		origin.block_telemetry()

	@staticmethod
	def handle_response(flow: HTTPFlow):
		origin = OriginPlatform(flow)
		origin.intercept_entitlements()
		origin.intercept_products()

	def intercept_entitlements(self):
		if self.host_and_path_match(
				host=r"^api\d*\.origin\.com$",
				path=r"^/ecommerce2/entitlements/\d+$"
		):  # Real DLC request
			if self.flow.request.headers['Accept'] == 'application/vnd.origin.v2+json':
				log.info('Intercepted an Entitlements request from Origin ')

				entitlements: List[Dict] = json.loads(self.flow.response.text)['entitlements']

				# FIXME: Cannot modify response since X-Origin-Signature header will not match
				# entitlements.append({
				# 	'productId': 'SIMS4.OFF.SOLP.0x0000000000028FE2',  # FIXME: IID
				# 	"entitlementTag": 'SP11_FitnessStuff_0x0000000000028FE2:167906',  # FIXME: ETG
				# 	'groupName': "THESIMS4PC",  # FIXME: GRP
				# 	"entitlementType": "DEFAULT",  # FIXME: TYP
				# 	"lastModifiedDate": "2020-01-01T00:00Z",
				# 	'entitlementSource': "ORIGIN-OIG",
				# 	"entitlementId": 1012953621293,  # FIXME: ?
				# 	"grantDate": "2020-01-01T00:00:00Z",
				# 	'suppressedBy': [],
				# 	"version": 0,
				# 	"isConsumable": False,
				# 	"productCatalog": "OFB",
				# 	'suppressedOffers': [],
				# 	"originPermissions": '0',
				# 	"useCount": 0,
				# 	"projectId": "123456",
				# 	"status": "ACTIVE"
				# })

				log.debug(json.dumps(entitlements, indent=2))
				self.flow.response.text = json.dumps({'entitlements': entitlements}, separators=(',', ':'))

	def intercept_products(self):
		if self.host_and_path_match(
				host=r"^api\d*\.origin\.com$",
				path=r"^/ecommerce2/products$"
		):  # Just for store page, no effect in game
			log.info('Intercepted a Products request from Origin')
			tree = ElementTree.fromstring(self.flow.response.text)

			for elem in tree.iter():
				# TODO: Log DLC ids
				if elem.tag == 'offer':
					log.debug(f"\t{elem.attrib['offerId']}")
				elif elem.tag == 'isOwned':
					elem.text = 'true'
				elif elem.tag == 'userCanPurchase':
					elem.text = 'false'

			self.flow.response.status_code = 200
			self.flow.response.reason = "OK"
			self.flow.response.text = ElementTree.tostring(tree, encoding='unicode')

	def block_telemetry(self):
		if config.block_telemetry and self.flow.request.path.startswith('/ratt/telm'):
			self.flow.response = HTTPResponse.make(500, 'No more spying')
			log.debug('Blocked telemetry request from Origin')

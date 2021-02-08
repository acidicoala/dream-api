from mitmproxy.http import HTTPFlow

from mitm.platforms.epic import EpicPlatform
from mitm.platforms.origin import OriginPlatform
from util.log import log


class DreamAPIAddon:
	@staticmethod
	def request(flow: HTTPFlow):
		try:
			EpicPlatform.handle_request(flow)
			# OriginPlatform.handle_request(flow)
		except Exception as e:
			log.exception(str(e))

	@staticmethod
	def response(flow: HTTPFlow):
		try:
			EpicPlatform.handle_response(flow)
			OriginPlatform.handle_response(flow)
		except BaseException as e:
			log.exception(str(e))

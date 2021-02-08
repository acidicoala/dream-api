import re
from abc import abstractmethod, ABC
from urllib.parse import urlparse

from mitmproxy.http import HTTPFlow


class BasePlatform(ABC):
	flow: HTTPFlow

	def __init__(self, flow: HTTPFlow):
		self.flow = flow

	@staticmethod
	@abstractmethod
	def handle_request(flow: HTTPFlow):
		pass

	@staticmethod
	@abstractmethod
	def handle_response(flow: HTTPFlow):
		pass

	def host_and_path_match(self, host: str, path: str):
		req_host = self.flow.request.pretty_host
		req_path = urlparse(self.flow.request.url).path

		return re.match(host, req_host) and re.match(path, req_path)

import re
from abc import ABC
from typing import List
from urllib.parse import urlparse

from mitmproxy.http import HTTPFlow

from util.log import log


def log_exceptions(func):
	def wrapper(*args, **kwargs):
		try:
			func(*args, **kwargs)
		except BaseException as e:
			log.exception(str(e))

	return wrapper


class BaseAddon(ABC):

	@staticmethod
	def request(flow: HTTPFlow):
		pass

	@staticmethod
	def response(flow: HTTPFlow):
		pass

	@staticmethod
	def block_telemetry(flow: HTTPFlow):
		pass

	@staticmethod
	def get_hosts(hosts: List[str]):
		return ''.join([rf'(?!{host}:)' for host in hosts])

	@staticmethod
	def host_and_path_match(flow: HTTPFlow, host: str, path: str):
		req_host = flow.request.pretty_host
		req_path = urlparse(flow.request.url).path

		return re.match(host, req_host) and re.match(path, req_path)

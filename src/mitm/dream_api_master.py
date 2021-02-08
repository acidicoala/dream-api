import asyncio
from threading import Thread

from mitmproxy.master import Master
from mitmproxy.options import Options
from mitmproxy.proxy import ProxyServer, ProxyConfig
from mitmproxy.tools.web.master import WebMaster

from mitm.dream_api_addon import DreamAPIAddon
from setup.config import config
from util.log import log


class DreamAPIMaster(WebMaster if config.use_webmaster else Master):
	def __init__(self):
		options = Options(
				listen_port=config.port,
				# Allow only epic & origin hosts for now
				ignore_hosts=[
					r'^(?![0-9.]+:)'  # All ip addresses
					r'(?!api\.epicgames\.dev:)'
					r'(?!api\d*\.origin\.com:)'
					r'(?!ecommerceintegration.+\.epicgames\.com:)'
				]
		)
		options.add_option("body_size_limit", int, 0, "")

		super().__init__(options)

		self.server = ProxyServer(ProxyConfig(options))
		self.addons.add(DreamAPIAddon())
		log.info(f'Successfully initialized mitmproxy on port {config.port}')

	def loop_in_thread(self):
		asyncio.set_event_loop(self.channel.loop)
		self.run()

	def run_async(self):
		Thread(target=self.loop_in_thread).start()

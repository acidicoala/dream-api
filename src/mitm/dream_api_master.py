import asyncio
from threading import Thread

from mitmproxy.master import Master
from mitmproxy.options import Options
from mitmproxy.proxy import ProxyServer, ProxyConfig
from mitmproxy.tools.web.master import WebMaster

from mitm.addons.epic import EpicAddon
from mitm.addons.origin import OriginAddon
from setup.config import config
from util.log import log


class DreamAPIMaster(WebMaster if config.use_webmaster else Master):
	def __init__(self):
		options = Options(
				listen_port=config.port,
				ignore_hosts=[''.join([
					r'^(?![0-9.]+:)',  # https://docs.mitmproxy.org/stable/howto-ignoredomains/
					EpicAddon.hosts,  # Allow epic hosts
					OriginAddon.hosts,  # Allow origin hosts
				])]
		)
		options.add_option("body_size_limit", int, 0, "")  # Fix for weird bug that crashes mitmproxy

		super().__init__(options)

		self.server = ProxyServer(ProxyConfig(options))
		self.addons.add(EpicAddon())
		self.addons.add(OriginAddon())

		log.info(f'Successfully initialized mitmproxy on port {config.port}')

	def loop_in_thread(self):
		asyncio.set_event_loop(self.channel.loop)
		self.run()

	def run_async(self):
		Thread(target=self.loop_in_thread).start()

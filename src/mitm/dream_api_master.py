import asyncio
from threading import Thread

from mitmproxy.master import Master
from mitmproxy.options import Options
from mitmproxy.proxy import ProxyServer, ProxyConfig

from mitm.dream_api_addon import DreamAPIAddon
from setup.config import Config
from util.log import Log


class DreamAPIMaster(Master):
	def __init__(self):
		options = Options(
				listen_port=Config().port,
				# Allow only epic & origin hosts for now
				ignore_hosts=[r'^(?![0-9\.]+:)(?!api\.epicgames\.dev:)(?!api\d*\.origin\.com:)']
		)
		options.add_option("body_size_limit", int, 0, "")

		super().__init__(options)

		self.server = ProxyServer(ProxyConfig(options))
		self.addons.add(DreamAPIAddon())
		Log().info(f'Successfully initialized mitmproxy on port {Config().port}')

	def loop_in_thread(self):
		asyncio.set_event_loop(self.channel.loop)
		# asyncio.set_event_loop(loop)
		self.run()

	def run_async(self):
		Thread(
				target=self.loop_in_thread,
		).start()

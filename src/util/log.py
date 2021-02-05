from logging import *

from util.info import version
from util.resource import get_data_path
from util.singleton import Singleton

log_path = get_data_path('DreamAPI.log')


class Log(Logger, metaclass=Singleton):
	def __new__(cls, **kwargs):
		logger = getLogger('DreamAPI')
		logger.setLevel(DEBUG)

		formatter = Formatter('[%(asctime)s.%(msecs)03d][%(levelname)s]\t%(message)s')
		formatter.datefmt = '%H:%M:%S'

		fileHandler = FileHandler(log_path, 'w')
		fileHandler.setFormatter(formatter)
		fileHandler.setLevel(DEBUG)

		consoleHandler = StreamHandler()
		consoleHandler.setFormatter(formatter)
		consoleHandler.setLevel(DEBUG)

		logger.addHandler(fileHandler)
		logger.addHandler(consoleHandler)

		return logger

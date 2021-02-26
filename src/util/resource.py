import sys
from pathlib import Path

is_production = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_bundle_path(name: str):
	if is_production:
		# noinspection PyProtectedMember
		return Path(sys._MEIPASS) / 'resources' / name
	else:
		return Path(sys.argv[0]).parent.parent / 'resources' / name


def get_data_path(name: str) -> Path:
	"""
	:param name: Relative path to file
	:return: In production, returns path under the working directory.
			In development, returns path under the ./dev_working_dir directory
	"""
	if is_production:
		return Path(sys.executable).parent / name
	else:
		return Path(sys.argv[0]).parent.parent / 'dev_working_dir' / name

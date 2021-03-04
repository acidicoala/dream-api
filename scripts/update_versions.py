# A script that automates the process of updating versions
# across multiple heterogeneous files

import re
import sys
from pathlib import Path
from typing import Tuple, List


def get_path(path: str):
	return Path(sys.path[0]).parent / path


def process_file(filePath: str, patterns: List[Tuple[str, str]]):
	with open(get_path(filePath), 'r') as file:
		lines = file.readlines()

	for pattern in patterns:
		regex, repl = pattern

		for index, line in enumerate(lines):
			lines[index] = re.sub(regex, repl, line)

	with open(get_path(filePath), 'w') as file:
		file.writelines(lines)


if __name__ == '__main__':
	VER_MAJOR = 1
	VER_MINOR = 2
	VER_PATCH = 0
	VER_REVISION = 0

	process_file('version_info.py', [
		(r'(filevers|prodvers)=\(.*\)', rf'\1=({VER_MAJOR}, {VER_MINOR}, {VER_PATCH}, {VER_REVISION})'),
		(r"u'(FileVersion|ProductVersion)', u'.*'", rf"u'\1', u'{VER_MAJOR}.{VER_MINOR}.{VER_PATCH}.{VER_REVISION}'")
	])

	process_file('inno_setup.iss', [
		(r'AppVersion ".+"', f'AppVersion "{VER_MAJOR}.{VER_MINOR}.{VER_PATCH}"'),
		(r'AppVersionLong ".+"', f'AppVersionLong "{VER_MAJOR}.{VER_MINOR}.{VER_PATCH}.{VER_REVISION}"'),
	])

	process_file('src/util/info.py', [
		(r"version = '.*'", f"version = 'v{VER_MAJOR}.{VER_MINOR}.{VER_PATCH}'"),
	])

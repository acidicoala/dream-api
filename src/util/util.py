import subprocess


def open_file_in_os(path: str):
	subprocess.run(['explorer', path], check=False)

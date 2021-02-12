import subprocess


def open_file_in_os(path: str):
	subprocess.run(['explorer', path], check=False)


def get_ex_msg(e: BaseException, default='Error'):
	return e.strerror if hasattr(e, 'strerror') else e.message if hasattr(e, 'message') else default

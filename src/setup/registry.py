from typing import Union

from winreg import *

from util.log import Log

internet_settings_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings'


def __set_reg(name, value: Union[str, int]):
	try:
		key = OpenKey(HKEY_CURRENT_USER, internet_settings_path, 0, KEY_WRITE)
		val_type = REG_DWORD if isinstance(value, int) else REG_SZ

		SetValueEx(key, name, 0, val_type, value)
		CloseKey(key)
		return True
	except WindowsError:
		return False


def __get_reg(name):
	try:
		key = OpenKey(HKEY_CURRENT_USER, internet_settings_path, 0, KEY_READ)
		value, regtype = QueryValueEx(key, name)
		CloseKey(key)
		return value
	except WindowsError:
		return None


def enable_proxy(port: int):
	__set_reg('ProxyEnable', 1)
	__set_reg('ProxyOverride', '<local>')
	__set_reg('ProxyServer', f'127.0.0.1:{port}')

	Log().info(f'Internet proxy enabled on 127.0.0.1:{port}')


def disable_proxy():
	__set_reg('ProxyEnable', 0)

	Log().info(f'Internet proxy disabled')

import os
import subprocess
from pathlib import Path

from win32api import FormatMessage

from util.log import log


def is_cert_installed():
	error_code = subprocess.call(f'certutil -store -user Root mitmproxy', shell=True)

	log.info(f"Certificate is {'not ' if error_code else ''}installed")
	return not bool(error_code)


def install_cert():
	log.warning('Installing mitmproxy certificate...')

	crtPath = Path.home().joinpath('.mitmproxy', 'mitmproxy-ca-cert.cer')

	if error_code := subprocess.call(f'certutil -addstore -user Root {crtPath}', shell=True):
		log.error(f'Certificate could not be installed: {str(FormatMessage(error_code)).strip()}')
		# noinspection PyProtectedMember,PyUnresolvedReferences
		os._exit(1)
	else:
		log.info('Certificate was successfully installed')


def delete_cert():
	log.warning('Deleting mitmproxy certificate...')
	if (error_code := subprocess.call('certutil -delstore -user Root mitmproxy', shell=True)) == 0:
		log.info('Certificate was successfully deleted')
	else:
		log.error(f'Certificate could not be deleted: {str(FormatMessage(error_code)).strip()}')

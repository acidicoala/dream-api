import ssl
from pathlib import Path

from cryptography import x509
from cryptography.x509 import NameOID
from mitmproxy.options import Options
from mitmproxy.proxy import ProxyConfig
from win32crypt import CryptStringToBinary, CertOpenStore
from win32cryptcon import *

from util.log import log


def is_cert_installed():
	for (cert_bytes, encoding_type, trust) in ssl.enum_certificates("ROOT"):
		cert = x509.load_der_x509_certificate(cert_bytes)
		attrs = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)

		if len(attrs) > 0:
			if attrs[0].value == 'mitmproxy':
				log.info('Certificate is installed')
				return True

	return False


def auto_install_cert():
	log.warning('Certificate is not installed. Installing...')

	# Create dummy config to generate certificate
	ProxyConfig(Options())

	crtPath = Path.home().joinpath('.mitmproxy', 'mitmproxy-ca-cert.cer')

	with open(crtPath, 'r') as f:
		cert_str = f.read()

	cert_byte = CryptStringToBinary(cert_str, CRYPT_STRING_BASE64HEADER)[0]

	# https://docs.microsoft.com/en-us/windows/win32/api/wincrypt/nf-wincrypt-certopenstore
	store = CertOpenStore(
			CERT_STORE_PROV_SYSTEM,
			0,
			None,
			CERT_SYSTEM_STORE_CURRENT_USER | CERT_STORE_OPEN_EXISTING_FLAG,
			"ROOT"
	)

	try:
		# https://docs.microsoft.com/en-us/windows/win32/api/wincrypt/nf-wincrypt-certaddencodedcertificatetostore
		store.CertAddEncodedCertificateToStore(
				X509_ASN_ENCODING,
				cert_byte,
				CERT_STORE_ADD_REPLACE_EXISTING
		)
		log.info('Certificate installation was successfully completed')
	except BaseException as e:
		log.error('Certificate installation was unsuccessful')
		log.exception(str(e))
	finally:
		store.CertCloseStore(CERT_CLOSE_STORE_FORCE_FLAG)

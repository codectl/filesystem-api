import requests
import tempfile
from pathlib import Path

from OpenSSL import crypto
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_ssh_private_key,
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)


key_path = "/Users/renato/.ssh/id_rsa"
key_bytes = Path(key_path).read_bytes()
openssh = load_ssh_private_key(key_bytes, None)

# convert to rsa format
pem_data = openssh.private_bytes(
    encoding=Encoding.PEM,
    format=PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=NoEncryption(),
)

pem = load_pem_private_key(pem_data, None)
pkey = crypto.PKey.from_cryptography_key(pem)

cert = crypto.X509()
cert.get_subject().commonName = "rena2damas"
cert.get_subject().organizationalUnitName = "private"
cert.get_subject().organizationName = "HOME"
cert.get_subject().countryName = "US"
cert.set_serial_number(1000)
cert.gmtime_adj_notBefore(0)
cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
cert.set_issuer(cert.get_subject())
cert.set_pubkey(pkey)
cert.sign(pkey, "sha1")

cer = tempfile.NamedTemporaryFile(mode="w+", suffix=".pem")
key = tempfile.NamedTemporaryFile(mode="w+", suffix=".key")
try:
    decoded_cer = cert.to_cryptography().public_bytes(Encoding.PEM).decode("utf-8")
    decoded_key = (
        pem.public_key()
        .public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)
        .decode("utf-8")
    )
    cer.write(decoded_cer)
    key.write(pem_data.decode("utf-8"))

    print(decoded_cer)
    print(decoded_key)
    print(pem_data.decode("utf-8"))

    cer.seek(0)
    key.seek(0)

    response = requests.get(
        "https://localhost:8080/",
        verify="ssl/server.crt",
        cert=("ssl/client.crt", "ssl/client.key"),
    )
    print(response)
finally:
    cer.close()
    key.close()

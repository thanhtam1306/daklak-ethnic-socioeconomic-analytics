"""
Setup Local SSL Certificates for DakLak DSS
Creates trusted local SSL certificate for https://dtts-daklak.com
"""

import os
import sys
import subprocess
import datetime
import ipaddress

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERTS_DIR = os.path.join(BASE_DIR, "certs")
os.makedirs(CERTS_DIR, exist_ok=True)

root_ca_crt_path = os.path.join(CERTS_DIR, "rootCA.crt")
root_ca_key_path = os.path.join(CERTS_DIR, "rootCA.key")
server_crt_path = os.path.join(CERTS_DIR, "cert.pem")
server_key_path = os.path.join(CERTS_DIR, "key.pem")

print("[1/3] Tao Root CA noi bo...")
root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
root_name = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "DakLak DSS Local Root CA"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DakLak Analytics DSS"),
    x509.NameAttribute(NameOID.COUNTRY_NAME, "VN"),
])

now = datetime.datetime.now(datetime.timezone.utc)
root_cert = (
    x509.CertificateBuilder()
    .subject_name(root_name)
    .issuer_name(root_name)
    .public_key(root_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - datetime.timedelta(days=1))
    .not_valid_after(now + datetime.timedelta(days=3650))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    .sign(root_key, hashes.SHA256())
)

with open(root_ca_key_path, "wb") as f:
    f.write(root_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

with open(root_ca_crt_path, "wb") as f:
    f.write(root_cert.public_bytes(serialization.Encoding.PEM))

print("[2/3] Tao Server SSL Certificate cho dtts-daklak.com...")
server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
server_name = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "dtts-daklak.com"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DakLak Analytics DSS"),
    x509.NameAttribute(NameOID.COUNTRY_NAME, "VN"),
])

san = x509.SubjectAlternativeName([
    x509.DNSName("dtts-daklak.com"),
    x509.DNSName("dss.daklak.gov.vn"),
    x509.DNSName("trolychinhsach.daklak.gov.vn"),
    x509.DNSName("localhost"),
    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
])

server_cert = (
    x509.CertificateBuilder()
    .subject_name(server_name)
    .issuer_name(root_name)
    .public_key(server_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - datetime.timedelta(days=1))
    .not_valid_after(now + datetime.timedelta(days=1825))
    .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    .add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    .add_extension(
        x509.ExtendedKeyUsage([
            x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
        ]),
        critical=False,
    )
    .add_extension(san, critical=False)
    .sign(root_key, hashes.SHA256())
)

with open(server_key_path, "wb") as f:
    f.write(server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

# Write full chain (server cert + root ca)
with open(server_crt_path, "wb") as f:
    f.write(server_cert.public_bytes(serialization.Encoding.PEM))
    f.write(root_cert.public_bytes(serialization.Encoding.PEM))

print("[3/3] Dang ky Root CA vao he dieu hanh Windows (Trusted Root)...")
try:
    res = subprocess.run(
        ["certutil", "-user", "-addstore", "-f", "Root", root_ca_crt_path],
        capture_output=True,
        text=True,
        check=True
    )
    print("Ket qua certutil (User Root):", res.stdout.strip())
except Exception as e:
    print("Canh bao khi chay certutil:", e)

print("\n>>> THANH CONG! Chung chi SSL da duoc tao va tin cay tren he thong.")
print(f"    Cert: {server_crt_path}")
print(f"    Key:  {server_key_path}")

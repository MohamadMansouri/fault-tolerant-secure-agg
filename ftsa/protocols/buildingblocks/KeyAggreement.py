"""
### **Key-Agreement Scheme**

This module contains a wraper for Elliptec Curve DH scheme over NIST256p the  from the library \"[Python Cryptography Toolkit (pycrypto)](https://cryptography.io/en/latest/)\"

"""

from ecdsa import ECDH, NIST256p
from Crypto.Hash import SHA256
from gmpy2 import mpz

class KAS(object):
    """A key-agreement class that holds the secret and public keys of a party"""
    curve = NIST256p
    """The curve used by the scheme (default: NIST256P)"""
    def __init__(self) -> None:
        super().__init__()
        self.ecdh = ECDH(KAS.curve)
        self.sk = None
        self.pk = None

    def generate(self):
        """Generates a key pair of public and private key"""
        self.pk = self.ecdh.generate_private_key()
        self.sk = self.ecdh.private_key
        return self

    def generate_from_bytes(self, bytes):
        """Generates the public key from the bytes of the private key"""
        self.pk = self.ecdh.load_private_key_bytes(bytes)
        self.sk = self.ecdh.private_key
        return self

    def agree(self, pk, size=256, pem=False):
        """Agree on a shared key of size `size` using the public key `pk` of the other party"""
        if not pem:
            self.ecdh.load_received_public_key(pk)
        else:
            self.ecdh.load_received_public_key_pem(pk)
        h = SHA256.new()
        h.update(self.ecdh.generate_sharedsecret_bytes())
        counter = 0
        result = b''
        while len(result) < (size // 8):
            h = SHA256.new()
            h.update(self.ecdh.generate_sharedsecret_bytes() + counter.to_bytes(1,"big"))
            result += h.digest()
            counter += 1
        r = mpz(int.from_bytes(result[-size:],"big"))
        return r

    def get_sk_bytes(self):
        """Returns the bytes of the secret key"""
        return self.sk.to_string()

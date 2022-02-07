from ecdsa import ECDH, NIST256p
from Crypto.Hash import SHA256
from gmpy2 import mpz

class KAS(object):
    curve = NIST256p
    def __init__(self) -> None:
        super().__init__()
        self.ecdh = ECDH(KAS.curve)
        self.sk = None
        self.pk = None

    def generate(self):
        self.pk = self.ecdh.generate_private_key()
        self.sk = self.ecdh.private_key
        return self

    def generate_from_bytes(self, bytes):
        self.pk = self.ecdh.load_private_key_bytes(bytes)
        self.sk = self.ecdh.private_key
        return self

    def agree(self, pk, size=256, pem=False):
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
        return self.sk.to_string()

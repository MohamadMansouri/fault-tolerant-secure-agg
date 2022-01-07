from protocols.utils.CommMeasure import getrealsize

from Crypto.Cipher import AES
from gmpy2 import mpz

class EncryptedMessage(object):
    def __init__(self, ciphertext, tag, nonce) -> None:
        super().__init__()
        self.ct = ciphertext
        self.tag = tag
        self.nonce = nonce

    def __repr__(self):
        return str(self.ct)

    def getrealsize(self):
        return getrealsize(self.ct) + getrealsize(self.tag) + getrealsize(self.nonce)


class EncryptionKey(object):
    def __init__(self, key) -> None:
        super().__init__()
        if isinstance(key, mpz):
            key = int(key)
        if isinstance(key, int):
            k = key
            if key >= 2**128:
                mask = 2**128 - 1
                k  &= mask 
            self.key = k.to_bytes(16, "big")
        elif isinstance(key, bytes):
            assert len(key) >= 16, "key size should be at least 16 bytes"
            self.key = key[:16]
            return
        else:
            raise ValueError("Key is of unacceptable type {}".format(type(key)))
    
    def encrypt(self, m):
        cipher = AES.new(self.key, AES.MODE_GCM)
        ct, tag = cipher.encrypt_and_digest(m)
        return EncryptedMessage(ct, tag, cipher.nonce)

    def decrypt(self, e : EncryptedMessage):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce = e.nonce)
        return cipher.decrypt_and_verify(e.ct,e.tag)
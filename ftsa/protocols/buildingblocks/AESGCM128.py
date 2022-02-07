"""
### **Authenticated Encryption Scheme**

This module contains a wraper for AES-GCM encryption from the library \"[Python Cryptography Toolkit (pycrypto)](https://cryptography.io/en/latest/)\"
"""

from ftsa.protocols.utils.CommMeasure import getrealsize

from Crypto.Cipher import AES
from gmpy2 import mpz

class EncryptedMessage(object):
    """
    An encrypted message using AES-GCM 

    ## **Args**:
    -------------
    *ciphertext* : `bytes` --
        the raw ciphertext value

    *tag* : `bytes` --
        the integrity verification tag raw value

    *nonce* : `byets`
        the nonce raw value
    
    ## **Attributes**:
    -------------
    *ciphertext* : `bytes` --
        the raw ciphertext value

    *tag* : `bytes` --
        the integrity verification tag raw value

    *nonce* : `bytes` --
        the nonce raw value
    """
    def __init__(self, ciphertext, tag, nonce) -> None:
        super().__init__()
        self.ct = ciphertext
        self.tag = tag
        self.nonce = nonce

    def __repr__(self):
        return str(self.ct)

    def getrealsize(self):
        """returns the size of the ciphertext in bits"""
        return getrealsize(self.ct) + getrealsize(self.tag) + getrealsize(self.nonce)


class EncryptionKey(object):
    """
    The AES-GCM key to be used for encryption/decryption of messages

    ## **Args**:
    -------------
    *key* : `bytes` or `int` or `gmpy2.mpz` --
        the raw key value

    ## **Attributes**:
    -------------
    *key* : `bytes` or `int` or `gmpy2.mpz` --
        the raw key value
    """
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
        """Encrypts the message m and returns an `EncryptedMessage`"""
        cipher = AES.new(self.key, AES.MODE_GCM)
        ct, tag = cipher.encrypt_and_digest(m)
        return EncryptedMessage(ct, tag, cipher.nonce)

    def decrypt(self, e : EncryptedMessage):
        """Decrypts and verfies the integrits of `EncryptedMessage` and returns the message bytes"""
        cipher = AES.new(self.key, AES.MODE_GCM, nonce = e.nonce)
        return cipher.decrypt_and_verify(e.ct,e.tag)
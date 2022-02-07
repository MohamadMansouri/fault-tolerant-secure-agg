from Crypto.Hash import SHA256
from gmpy2 import mpz, gcd



class FDH(object):
    def __init__(self, keysize, n) -> None:
        super().__init__()
        self.keysize = keysize
        self.n = n

    def H(self, t):
        counter = 1
        result = b''
        while True:
            while True:
                h = SHA256.new()
                h.update(int(t).to_bytes(self.keysize // 2,"big") + counter.to_bytes(1,"big"))
                result += h.digest()
                counter += 1
                if len(result) < (self.keysize // 8):
                    break
            r = mpz(int.from_bytes(result[-self.keysize:],"big"))
            if gcd(r, self.n) == 1:
                break
            else:
                print("HAPPENED")
        return r

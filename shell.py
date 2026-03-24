# from database import Transaction
# import asyncio
# import main
# from config.tortoise import init 
    #Python
# run pip install pycryptodome to use the GCM Mode
import json
from Crypto.Cipher import AES
from Crypto import Random
import base64
from binascii import hexlify as hexa
# async def script():

def encryptAES256():
    encryptionKey = ...
    paymentData = {
        "reference": "12345678",
        "card": {
          	"name": "Gbekeloluwa Oyemakinde",
            "number": ...,
            "cvv": ...,
            "expiry_month": ...,
            "expiry_year": ...,
            # "pin": "0000" // optional
        },
        "amount": 1000,
        "currency": "NGN",
        "redirect_url": "https://merchant-redirect-url.com",
        "customer": {
            "name": "Gbekeloluwa Oyemakinde",
            "email": "johndoe@korapay.com"
        },
 
    }
    paymentData = json.dumps(paymentData)
    try:
        iv = Random.get_random_bytes(16)
        encObj = AES.new(encryptionKey.encode("utf8"), AES.MODE_GCM, iv)
        cipherText,authTag = encObj.encrypt_and_digest(paymentData.encode("utf8"))
        iv64 = base64.b64encode(iv).decode('ascii')
        ivToHex = hexa(iv).decode()
        cipherTextToHex = hexa(cipherText).decode()
        authTagToHex = hexa(authTag).decode()
        result = ivToHex + ":" + cipherTextToHex + ":" + authTagToHex
        print(result)
        return result
    except Exception as e:
        print(e)
    return 

if __name__ == '__main__':
    print('running')
    encryptAES256()
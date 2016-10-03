# Output of the script is encrypted using this key. 
# Server used that secret to decrypt the message.
SECRET_KEY = 'crossOverNaxi9f'

import time
import json
import psutil
import base64
from Crypto.Cipher import AES


def encrypt(text):
    text += ' ' * (16 - len(text)%16)
    secret = SECRET_KEY + 'x' * (16 - len(SECRET_KEY)%16)
    cipher = AES.new(secret, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(text))

def decrypt(decoded):
    secret = SECRET_KEY + 'x' * (16 - len(SECRET_KEY)%16)
    cipher = AES.new(secret, AES.MODE_ECB)
    return cipher.decrypt(base64.b64decode(decoded)).strip()

if __name__ == '__main__':
    metrics = {
        'cpu_percent': psutil.cpu_percent(),
        'mem_percent': psutil.virtual_memory().percent,
        'uptime_sec': int(time.time() - psutil.boot_time())
    }

    try:
        import win32api
        metrics['event_log'] = 'NotImplemented'
    except ImportError:
        pass

    print(encrypt(json.dumps(metrics)))

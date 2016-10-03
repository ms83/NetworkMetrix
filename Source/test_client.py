import os
import json
from client import decrypt

def test_decoding():
    stdout = os.popen("python client.py").read()
    json_str = decrypt(stdout)
    d = json.loads(json_str)
    assert type(d) == dict

from client import encrypt, decrypt

def test_crypt():
    msg = 'this is a secret message'
    assert msg == decrypt(encrypt(msg))

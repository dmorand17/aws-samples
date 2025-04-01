import base64
import os

# key length in bytes
key_length = 128

key = base64.b64encode(os.urandom(key_length)).decode("utf-8")

print(f"MUNGE_KEY={key}")

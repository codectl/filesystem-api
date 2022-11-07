import os
import jwt
import requests
from pathlib import Path
from cryptography.hazmat.primitives.serialization import load_ssh_private_key

username = os.getlogin()  # current username
data = Path(os.path.join(Path.home(), ".ssh", "id_rsa")).read_bytes()
key = load_ssh_private_key(data, password=None)
token = jwt.encode({"sub": username}, key, algorithm="RS256")

url = "https://..."  # complete url
headers = {"Authorization": f"Bearer {token}"}
r = requests.get(url=url, headers=headers)
# handle response data

print(jwt.decode(token, options={"verify_signature": False}))

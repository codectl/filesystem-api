import tempfile

import requests


# edit these variables accordingly
base_url = "http://localhost:5000/api/filesystem/v1"
username = "renato"
password = "password"

# create a sample temporary file
directory = "/tmp"
filename = "sample.txt"
content = b"This is a sample"
tmp = tempfile.TemporaryFile()
tmp.write(content)
tmp.seek(0)

# POST request
r = requests.post(
    url=f"{base_url}/filesystem/{directory}",
    headers={"accept": "application/json"},
    auth=(username, password),
    files={"files": (filename, tmp)},
)

tmp.close()  # delete file

assert r.status_code in (201, 400)  # file may already exist

# GET request (json format)
r = requests.get(
    url=f"{base_url}/filesystem/{directory}/",
    headers={"accept": "application/json"},
    auth=(username, password),
)

assert r.status_code == 200
assert "sample.txt" in r.json()

# GET request (bytes format)
# works for dirs too, but careful with dir size!
r = requests.get(
    url=f"{base_url}/filesystem/{directory}/{filename}",
    headers={"accept": "application/octet-stream"},
    auth=(username, password),
    stream=True,
)

assert r.status_code == 200
assert r.raw.read() == content

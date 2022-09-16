import os
import tempfile

import requests


# edit these variables accordingly
base_url = "http://localhost:5000/api/filesystem/v1"
username = os.environ["USERNAME"]
password = os.environ["PASSWORD"]

# create a sample temporary file
directory = "tmp"
filename = "sample.txt"
content = b"This is a sample"

# POST request to create resource
with tempfile.TemporaryFile() as f:
    f.write(content)
    f.seek(0)
    r = requests.post(
        url=f"{base_url}/{directory}",
        headers={"accept": "application/json"},
        auth=(username, password),
        files={"files": (filename, f)},
    )

assert r.status_code == 201

# GET request (json format)
r = requests.get(
    url=f"{base_url}/{directory}/",
    headers={"accept": "application/json"},
    auth=(username, password),
)

assert r.status_code == 200
assert "sample.txt" in r.json()

# GET request (bytes format)
# works for dirs too, but careful with dir size!
r = requests.get(
    url=f"{base_url}/{directory}/{filename}",
    headers={"accept": "application/octet-stream"},
    auth=(username, password),
    stream=True,
)

assert r.status_code == 200
assert r.raw.read() == content

# PUT request for resource update (content is overridden)
r = requests.put(
    url=f"{base_url}/{directory}/",
    headers={"accept": "application/json"},
    auth=(username, password),
    files={"files": (filename, b"updated content")},
)

assert r.status_code == 204

# DELETE request for resource deletion
r = requests.delete(
    url=f"{base_url}/{directory}/{filename}",
    headers={"accept": "application/json"},
    auth=(username, password),
)

assert r.status_code == 204

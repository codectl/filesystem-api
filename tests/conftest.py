import pytest


@pytest.fixture(scope="function")
def file(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("this is a sample file")
    yield file
    file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def filedir(tmp_path):
    tmpdir = tmp_path / "dir"
    tmpdir.mkdir()
    yield tmpdir
    for f in tmpdir.iterdir():
        f.unlink() if f.is_file() else f.rmdir()
    tmpdir.rmdir()

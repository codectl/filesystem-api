import pytest


@pytest.fixture(scope="function")
def file(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("this is a sample file")
    yield file


@pytest.fixture(scope="function")
def filedir(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("dir")
    yield tmpdir

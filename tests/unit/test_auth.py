import pytest

from src.services.auth import impersonate


def test_impersonate(mocker):

    mocker.patch("os.setuid")
    mocker.patch("os.setgid")

    @impersonate(username="test")
    def decorated_test():
        pass

    mocker.patch("src.utils.user_uid", side_effect=KeyError)
    decorated_test()  # KeyError was suppressed
    mocker.patch("src.utils.user_uid", side_effect=TypeError)
    decorated_test()  # TypeError was suppressed
    mocker.patch("src.utils.user_uid", side_effect=PermissionError)
    decorated_test()  # PermissionError was suppressed
    mocker.patch("src.utils.user_uid", side_effect=Exception)
    with pytest.raises(Exception):
        decorated_test()  # no other exception is suppressed

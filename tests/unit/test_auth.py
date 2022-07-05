from src.services.auth import impersonate


def test_impersonate():
    @impersonate(username="test")
    def decorated_test():
        pass

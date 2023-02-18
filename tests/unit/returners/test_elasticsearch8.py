
import pytest
import saltext.elasticsearch8.returners.elasticsearch8_mod as elasticsearch8_returner


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"this_does_not_exist.please_replace_it": lambda: True},
    }
    return {
        elasticsearch8_returner: module_globals,
    }


def test_replace_this_this_with_something_meaningful():
    assert "this_does_not_exist.please_replace_it" in elasticsearch8_returner.__salt__
    assert elasticsearch8_returner.__salt__["this_does_not_exist.please_replace_it"]() is True

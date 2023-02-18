import pytest
import salt.modules.test as testmod
import saltext.elasticsearch8.modules.elasticsearch8_mod as elasticsearch8_module


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"test.echo": testmod.echo},
    }
    return {
        elasticsearch8_module: module_globals,
    }


def test_replace_this_this_with_something_meaningful():
    echo_str = "Echoed!"
    assert elasticsearch8_module.example_function(echo_str) == echo_str

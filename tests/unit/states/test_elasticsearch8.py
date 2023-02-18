import pytest
import salt.modules.test as testmod
import saltext.elasticsearch8.modules.elasticsearch8_mod as elasticsearch8_module
import saltext.elasticsearch8.states.elasticsearch8_mod as elasticsearch8_state


@pytest.fixture
def configure_loader_modules():
    return {
        elasticsearch8_module: {
            "__salt__": {
                "test.echo": testmod.echo,
            },
        },
        elasticsearch8_state: {
            "__salt__": {
                "elasticsearch8.example_function": elasticsearch8_module.example_function,
            },
        },
    }


def test_replace_this_this_with_something_meaningful():
    echo_str = "Echoed!"
    expected = {
        "name": echo_str,
        "changes": {},
        "result": True,
        "comment": "The 'elasticsearch8.example_function' returned: '{}'".format(echo_str),
    }
    assert elasticsearch8_state.exampled(echo_str) == expected

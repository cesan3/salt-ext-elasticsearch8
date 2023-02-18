
"""
Salt state module
"""
import logging

log = logging.getLogger(__name__)

__virtualname__ = "elasticsearch8"


def __virtual__():
    # To force a module not to load return something like:
    #   return (False, "The elasticsearch8 state module is not implemented yet")

    # Replace this with your own logic
    if "elasticsearch8.example_function" not in __salt__:
        return False, "The 'elasticsearch8' execution module is not available"
    return __virtualname__


def exampled(name):
    """
    This example function should be replaced
    """
    ret = {"name": name, "changes": {}, "result": False, "comment": ""}
    value = __salt__["elasticsearch8.example_function"](name)
    if value == name:
        ret["result"] = True
        ret["comment"] = "The 'elasticsearch8.example_function' returned: '{}'".format(value)
    return ret

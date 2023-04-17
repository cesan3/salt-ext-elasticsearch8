"""
Salt returner module
"""
import logging

log = logging.getLogger(__name__)

__virtualname__ = "elasticsearch8"


def __virtual__():
    # To force a module not to load return something like:
    #   return (False, "The elasticsearch8 returner module is not implemented yet")
    return (False, "The elasticsearch8 returner module is not implemented yet")

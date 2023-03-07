import pytest
import salt.modules.cp as cp
import saltext.elasticsearch8.states.elasticsearch8_mod as elasticsearch8_state

from tests.support.mock import MagicMock
from tests.support.mock import patch
from tests.support.unit import TestCase


NO_ELASTIC = False
WRONG_ELASTIC = False
try:
    import elasticsearch as elastic

    ES_MAJOR_VERSION = elastic.__version__[0]
    if ES_MAJOR_VERSION < 8:
        WRONG_ELASTIC = True
except Exception:  # pylint: disable=broad-except
    NO_ELASTIC = True


def get_es_config(key):
    config_es = {
        "elasticsearch": {
            "host": "http://localhost:9200"
        }
    }
    return config_es.get(key)


@pytest.mark.skipif(
    NO_ELASTIC,
    reason="Install elasticsearch-py before running Elasticsearch unit tests.",
)
@pytest.mark.skipif(
    WRONG_ELASTIC,
    reason="Elasticsearch-py version is incorrect for these unit tests.",
)
@pytest.fixture
def configure_loader_modules():
    index_get_result = {"test1": {"abcd"}}
    module_globals = {
        "__salt__": {
            "config.option": get_es_config,
            "cp.get_file_str": cp.get_file_str,
            "elasticsearch.index_get": MagicMock(return_value=index_get_result)
        },
        "__opts__": {}
    }
    return {
        elasticsearch8_state: module_globals,
    }


class ElasticsearchTestCase(TestCase):
    """
    Elasticsearch TestCase
    """
    def setUp(self):
        self.__opts__ = {"test": True}

    def tearDown(self):
        del self.__opts__

    def test_index_absent_test(self, hosts=None, profile=None):  # pylint: disable=unused-argument
        """
        Test of the index_absent method
        """
        result = {
            "name": "test1",
            "changes": {"old": {"abcd"}},
            "result": None,
            "comment": "Index test1 will be removed"
        }
        with patch.object(elasticsearch8_state, "__opts__", MagicMock(return_value=self.__opts__)):
            assert elasticsearch8_state.index_absent("test1") == result

#    def test_index_absent_no_test(self, hosts=None, profile=None):
#        """
#        """
#        self.__opts__ = {}
#        result = {
#            "name": "test1",
#            "changes": {"old": {"abcd"}},
#            "result": True,
#            "comment": "Successfully removed index test1"
#        }
#        with patch.object(elasticsearch8_state, "__opts__", MagicMock(return_value=self.__opts__)):
#            assert elasticsearch8_state.index_absent("test1") == result

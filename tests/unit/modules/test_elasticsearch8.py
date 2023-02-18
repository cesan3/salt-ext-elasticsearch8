# pylint: disable=too-many-lines
import pytest
import salt.modules.cp as cp
import saltext.elasticsearch8.modules.elasticsearch8_mod as elasticsearch8_module
from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError

from tests.support.elasticsearch.elasticsearch_mock8 import MockElastic
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
    module_globals = {
        "__salt__": {
            "config.option": get_es_config,
            "cp.get_file_str": cp.get_file_str
        },
    }
    return {
        elasticsearch8_module: module_globals,
    }


class ElasticsearchTestCase(TestCase):
    """
    Test cases for salt.modules.elasticsearch 8+
    """

    @staticmethod
    def es_return_true(hosts=None, profile=None):
        # pylint: disable=unused-argument
        return True

    @staticmethod
    def es_raise_command_execution_error(hosts=None, profile=None):
        # pylint: disable=unused-argument
        raise CommandExecutionError("custom message")

    # 'ping' function tests: 2

    def test_ping(self):
        """
        Test if ping succeeds
        """
        with patch.object(elasticsearch8_module, "_get_instance", self.es_return_true):
            assert elasticsearch8_module.ping()

    def test_ping_failure(self):
        """
        Test if ping fails
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", self.es_raise_command_execution_error
        ):
            assert not elasticsearch8_module.ping()

    # 'info' function tests: 2

    def test_info(self):
        """
        Test if status fetch succeeds
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.info() == [{"test": "key"}]

    def test_info_failure(self):
        """
        Test if status fetch fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(CommandExecutionError, elasticsearch8_module.info)

    # 'node_info' function tests: 2

    def test_node_info(self):
        """
        Test if node status fetch succeeds
        """

        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.node_info() == [{"test": "key"}]

    def test_node_info_failure(self):
        """
        Test if node status fetch fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(CommandExecutionError, elasticsearch8_module.node_info)

    def test_cluster_allocation_explain(self):
        """
        Test if cluster allocation explain succeeds
        """
        expected = {"allocate_explanation": "foo", "can_allocate": "no"}
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.cluster_allocation_explain() == expected

    def test_cluster_allocation_explain_failure(self):
        """
        Test if cluster allocation explain failure
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.cluster_allocation_explain
            )

    def test_cluster_pending_tasks(self):
        """
        Test if cluster pending tasks succeeds
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.cluster_pending_tasks() == {}

    def test_cluster_pending_tasks_failure(self):
        """
        Test if cluster pending tasks failure
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.cluster_pending_tasks
            )

    # 'cluster_health' function tests: 2

    def test_cluster_health(self):
        """
        Test if cluster status health fetch succeeds
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.cluster_health() == [{"test": "key"}]

    def test_cluster_health_failure(self):
        """
        Test if cluster status health fetch fails with CommandExecutionError
        """

        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(CommandExecutionError, elasticsearch8_module.cluster_health)

    # 'cluster_stats' function tests: 2

    def test_cluster_stats(self):
        """
        Test if cluster stats fetch succeeds
        """

        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.cluster_stats() == [{"test": "key"}]

    def test_cluster_stats_failure(self):
        """
        Test if cluster stats fetch fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(CommandExecutionError, elasticsearch8_module.cluster_stats)

    # 'alias_create' function tests: 3

    def test_alias_create(self):
        """
        Test if alias is created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.alias_create("foo", "bar")

    def test_alias_create_unack(self):
        """
        Test if alias creation is not acked
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.alias_create("foo", "bar")

    def test_alias_create_failure(self):
        """
        Test if alias creation fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.alias_create,
                "foo",
                "bar",
            )

    # 'alias_delete' function tests: 3

    def test_alias_delete(self):
        """
        Test if alias is deleted
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.alias_delete("foo", "bar")

    def test_alias_delete_unack(self):
        """
        Test if alias deletion is not acked
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.alias_delete("foo", "bar")

    def test_alias_delete_failure(self):
        """
        Test if alias deletion fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.alias_delete, "foo", "bar"
            )

    # 'alias_exists' function tests: 3

    def test_alias_exists(self):
        """
        Test if alias exists
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.alias_exists("foo", "bar")

    def test_alias_exists_not(self):
        """
        Test if alias doesn't exist
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert not elasticsearch8_module.alias_exists("foo", "bar")

    def test_alias_exists_failure(self):
        """
        Test if alias status obtain fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.alias_exists, "foo", "bar"
            )

    # 'alias_get' function tests: 3

    def test_alias_get(self):
        """
        Test if alias can be obtained
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.alias_get("foo", "bar") == {"test": "key"}

    def test_alias_get_not(self):
        """
        Test if alias doesn't exist
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.alias_get("foo", "bar") is None

    def test_alias_get_failure(self):
        """
        Test if alias obtain fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.alias_get, "foo", "bar"
            )

    # 'document_create' function tests: 2

    def test_document_create(self):
        """
        Test if document can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.document_create("foo", "bar") == {"test": "key"}

    def test_document_create_failure(self):
        """
        Test if document creation fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.document_create, "foo", "bar"
            )

    # 'document_delete' function tests: 2

    def test_document_delete(self):
        """
        Test if document can be deleted
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.document_delete("foo", "bar", "baz") == {"test": "key"}

    def test_document_delete_failure(self):
        """
        Test if document deletion fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.document_delete,
                "foo",
                "bar",
                "baz",
            )

    # 'document_exists' function tests: 3

    def test_document_exists(self):
        """
        Test if document status can be obtained
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.document_exists("foo", "bar")

    def test_document_exists_not(self):
        """
        Test if document doesn't exist
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert not elasticsearch8_module.document_exists("foo", "bar")

    def test_document_exists_failure(self):
        """
        Test if document exist state fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.document_exists, "foo", "bar"
            )

    # 'document_get' function tests: 3

    def test_document_get(self):
        """
        Test if document exists
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.document_get("foo", "bar") == {"test": "key"}

    def test_document_get_not(self):
        """
        Test if document doesn't exit
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.document_get("foo", "bar") is None

    def test_document_get_failure(self):
        """
        Test if document obtain fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.document_get, "foo", "bar"
            )

    # 'index_create' function tests: 5

    def test_index_create(self):
        """
        Test if index can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_create("foo", "bar")

    def test_index_create_no_shards(self):
        """
        Test if index is created and no shards info is returned
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(shards=False)),
        ):
            assert elasticsearch8_module.index_create("foo", "bar")

    def test_index_create_not_shards(self):
        """
        Test if index is created and shards didn't acked
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack_shards=False)),
        ):
            assert not elasticsearch8_module.index_create("foo", "bar")

    def test_index_create_not(self):
        """
        Test if index is created and shards didn't acked
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False, ack_shards=False)),
        ):
            assert not elasticsearch8_module.index_create("foo", "bar")

    def test_index_create_failure(self):
        """
        Test if index creation fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_create, "foo", "bar"
            )

    # 'index_delete' function tests: 3

    def test_index_delete(self):
        """
        Test if index can be deleted
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_delete("foo", "bar")

    def test_index_delete_not(self):
        """
        Test if index is deleted and shards didn't acked
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.index_delete("foo", "bar")

    def test_index_delete_failure(self):
        """
        Test if index deletion fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_delete, "foo", "bar"
            )

    # 'index_exists' function tests: 3

    def test_index_exists(self):
        """
        Test if index exists
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_exists("foo", "bar")

    def test_index_exists_not(self):
        """
        Test if index doesn't exist
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert not elasticsearch8_module.index_exists("foo", "bar")

    def test_index_exists_failure(self):
        """
        Test if alias exist state fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_exists, "foo", "bar"
            )

    def test_index_get_settings(self):
        """
        Test if settings can be obtained from the index
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_get_settings("foo", "bar") == {"foo": "key"}

    def test_index_get_settings_not_exists(self):
        """
        Test index_get_settings if index doesn't exist
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.index_get_settings(index="foo") is None

    def test_get_settings_failure(self):
        """
        Test if index settings get fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_get_settings, index="foo"
            )

    def test_index_put_settings(self):
        """
        Test if we can put settings for the index
        """
        settings = {"settings": {"index": {"number_of_replicas": 2}}}
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_put_settings(index="foo", settings=settings)

    def test_index_put_settings_not_exists(self):
        """
        Test if settings put executed against non-existing index
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.index_put_settings(index="foo") is None

    def test_index_put_settings_failure(self):
        """
        Test if settings put failed with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.index_put_settings,
                index="foo",
            )

    # 'index_get' function tests: 3

    def test_index_get(self):
        """
        Test if index can be obtained
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_get("foo", "bar") == {"test": "key"}

    def test_index_get_not(self):
        """
        Test if index doesn't exist
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.index_get("foo", "bar") is None

    def test_index_get_failure(self):
        """
        Test if index obtain fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_get, "foo", "bar"
            )

    # 'index_open' function tests: 3

    def test_index_open(self):
        """
        Test if index can be opened
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_open("foo", "bar")

    def test_index_open_not(self):
        """
        Test if index open isn't acked
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.index_open("foo", "bar")

    def test_index_open_failure(self):
        """
        Test if alias opening fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_open, "foo", "bar"
            )

    # 'index_close' function tests: 3

    def test_index_close(self):
        """
        Test if index can be closed
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_close("foo", "bar")

    def test_index_close_not(self):
        """
        Test if index close isn't acked
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.index_close("foo", "bar")

    def test_index_close_failure(self):
        """
        Test if index closing fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_close, "foo", "bar"
            )

    # 'mapping_create' function tests: 3

    def test_mapping_create(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.mapping_create("foo", "bar", "baz")

    def test_mapping_create_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.mapping_create("foo", "bar", "baz")

    def test_mapping_create_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.mapping_create, "foo", "bar", "baz"
            )

    # 'mapping_get' function tests: 3

    def test_mapping_get(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.mapping_get("foo", "bar", "baz") == {"test": "key"}

    def test_mapping_get_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.mapping_get("foo", "bar", "baz") is None

    def test_mapping_get_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.mapping_get, "foo", "bar", "baz"
            )

    # 'index_template_create' function tests: 3

    def test_index_template_create(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_template_create("foo", "bar")

    def test_index_template_create_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.index_template_create("foo", "bar")

    def test_index_template_create_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_template_create, "foo", "bar"
            )

    # 'index_template_delete' function tests: 3

    def test_index_template_delete(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_template_delete("foo")

    def test_index_template_delete_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.index_template_delete("foo")

    def test_index_template_delete_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_template_delete, "foo"
            )

    # 'index_template_exists' function tests: 3

    def test_index_template_exists(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_template_exists("foo")

    def test_index_template_exists_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert not elasticsearch8_module.index_template_exists("foo")

    def test_index_template_exists_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_template_exists, "foo"
            )

    # 'template_exists' function tests: 3

    def test_template_exists(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.template_exists("foo")

    def test_template_exists_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert not elasticsearch8_module.template_exists("foo")

    def test_template_exists_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.template_exists, "foo"
            )

    # 'index_template_get' function tests: 3

    def test_index_template_get(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.index_template_get("foo") == {"test": "key"}

    def test_index_template_get_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.index_template_get("foo") is None

    def test_index_template_get_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.index_template_get, "foo"
            )

    # 'pipeline_get' function tests: 4

    def test_pipeline_get(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.pipeline_get("foo") == {"test": "key"}

    def test_pipeline_get_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.pipeline_get("foo") is None

    def test_pipeline_get_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(CommandExecutionError, elasticsearch8_module.pipeline_get, "foo")

    def test_pipeline_get_wrong_version(self):
        """
        Test if mapping creation fails with CEE on invalid elasticsearch-py version
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(no_ingest=True)),
        ):
            pytest.raises(CommandExecutionError, elasticsearch8_module.pipeline_get, "foo")

    # 'pipeline_delete' function tests: 4

    def test_pipeline_delete(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.pipeline_delete("foo")

    def test_pipeline_delete_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.pipeline_delete("foo")

    def test_pipeline_delete_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.pipeline_delete, "foo"
            )

    def test_pipeline_delete_wrong_version(self):
        """
        Test if mapping creation fails with CEE on invalid elasticsearch-py version
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(no_ingest=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.pipeline_delete, "foo"
            )

    # 'pipeline_create' function tests: 4

    def test_pipeline_create(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.pipeline_create("foo")

    def test_pipeline_create_not(self):
        """
        Test if mapping creation didn't ack
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.pipeline_create("foo", "bar")

    def test_pipeline_create_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.pipeline_create, "foo", "bar"
            )

    def test_pipeline_create_wrong_version(self):
        """
        Test if mapping creation fails with CEE on invalid elasticsearch-py version
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(no_ingest=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.pipeline_create, "foo", "bar"
            )

    # 'pipeline_simulate' function tests: 3

    def test_pipeline_simulate(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.pipeline_simulate("foo", "bar") == {"test": "key"}

    def test_pipeline_simulate_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.pipeline_simulate, "foo", "bar"
            )

    def test_pipeline_simulate_wrong_version(self):
        """
        Test if mapping creation fails with CEE on invalid elasticsearch-py version
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(no_ingest=True)),
        ):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.pipeline_simulate, "foo", "bar"
            )

    def test_geo_ip_stats(self):
        """
        Test the method geo_ip_stats
        """
        expected = {
            "stats": {
                "successful_downloads": 0,
                "failed_downloads": 0,
                "total_download_time": 0,
                "databases_count": 0,
                "skipped_updates": 0,
                "expired_databases": 0,
            },
            "nodes": {},
        }
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.geo_ip_stats() == expected

    def test_processor_grok(self):
        """
        Test the method processor_grok
        """
        expected = {"patterns": {}}
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.processor_grok() == expected

    # 'script_get' function tests: 3

    def test_script_get(self):
        """
        Test search template
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.script_get("foo") == {"test": "key"}

    def test_script_get_not(self):
        """
        Test if mapping can be created
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.script_get("foo") is None

    def test_script_get_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(CommandExecutionError, elasticsearch8_module.script_get, "foo")

    # 'script_create' function tests: 3

    def test_script_create(self):
        """
        Test if search template can be created
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.script_create("foo", "bar")

    def test_script_create_not(self):
        """
        Test if search template can be created
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.script_create("foo", "bar")

    def test_script_create_failure(self):
        """
        Test if mapping creation fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.script_create,
                "foo",
                "bar",
            )

    # 'script_delete' function tests: 4

    def test_script_delete(self):
        """
        Test if mapping can be deleted
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.script_delete("foo")

    def test_script_delete_not(self):
        """
        Test if mapping can be deleted but not acked
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(ack=False)),
        ):
            assert not elasticsearch8_module.script_delete("foo")

    def test_script_delete_not_exists(self):
        """
        Test if deleting mapping doesn't exist
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(found=False)),
        ):
            assert elasticsearch8_module.script_delete("foo")

    def test_script_delete_failure(self):
        """
        Test if mapping deletion fails
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(CommandExecutionError, elasticsearch8_module.script_delete, "foo")

    # Cluster settings tests below.
    # We're assuming that _get_instance is properly tested
    # These tests are very simple in nature, mostly checking default arguments.
    def test_cluster_get_settings_succeess(self):
        """
        Test if cluster get_settings fetch succeeds
        """
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.cluster_get_settings() == {"transient": {}, "persistent": {}}

    def test_cluster_get_settings_failure(self):
        """
        Test if cluster get_settings fetch fails with CommandExecutionError
        """
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(CommandExecutionError, elasticsearch8_module.cluster_get_settings)

    def test_cluster_put_settings_succeess(self):
        """
        Test if cluster put_settings succeeds
        """
        expected_settings = {
            "acknowledged": True,
            "transient": {},
            "persistent": {"indices": {"recovery": {"max_bytes_per_sec": "50mb"}}},
        }
        transient = {}
        persistent = {"indices.recovery.max_bytes_per_sec": "50mb"}
        with patch.object(
            elasticsearch8_module, "_get_instance", MagicMock(return_value=MockElastic())
        ):
            assert elasticsearch8_module.cluster_put_settings(
                transient=transient, persistent=persistent
            ), expected_settings

    def test_cluster_put_settings_failure(self):
        """
        Test if cluster put_settings fails with CommandExecutionError
        """

        transient = {}
        persistent = {"indices.recovery.max_bytes_per_sec": "50mb"}
        with patch.object(
            elasticsearch8_module,
            "_get_instance",
            MagicMock(return_value=MockElastic(failure=True)),
        ):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.cluster_put_settings,
                persistent=persistent,
                transient=transient
            )

    def test_cluster_put_settings_nobody(self):
        """
        Test if cluster put_settings fails with SaltInvocationError
        """
        pytest.raises(SaltInvocationError, elasticsearch8_module.cluster_put_settings)

    def test_flush_succeeds(self):
        """
        Test if flush_synced succeeds
        """
        expected_return = {"_shards": {"failed": 0, "successful": 0, "total": 0}}
        sargs = {
            "index": "_all",
            "ignore_unavailable": True,
            "allow_no_indices": True,
            "expand_wildcards": "all",
        }
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.flush(**sargs) == expected_return

    def test_flush_failure(self):
        """
        Test if flush_synced fails with CommandExecutionError
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(CommandExecutionError, elasticsearch8_module.flush)

    def test_snapshot_get_repository(self):
        """
        Test snapshot get repository
        """
        expected_return = {
            "foo": {
                "type": "hdfs",
                "settings": {
                    "path": "elastic_snapshots",
                    "max_restore_bytes_per_sec": "1024mb",
                    "uri": "hdfs://foo.host:9000",
                    "max_snapshot_bytes_per_sec": "1024mb",
                },
            }
        }
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.repository_get(name="foo") == expected_return

    def test_snapshot_get_repository_not(self):
        """
        Test snapshot get repository
        """
        fake_es = MagicMock(return_value=MockElastic(found=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.repository_get("foo") is None

    def test_snapshot_get_repository_failure(self):
        """
        Test snapshot get repository
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.repository_get, name="foo"
            )

    def test_snapshot_create_repository(self):
        """
        Test snapshot create repository
        """
        body = {
            "type": "hdfs",
            "settings": {
                "path": "elastic_snapshots",
                "max_restore_bytes_per_sec": "1024mb",
                "uri": "hdfs://foo.host:9000",
                "max_snapshot_bytes_per_sec": "1024mb",
            },
        }
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.repository_create(name="foo", body=body)

    def test_snapshot_create_repository_not(self):
        """
        Test snapshot create repository with false ack
        """
        body = {
            "type": "hdfs",
            "settings": {
                "path": "elastic_snapshots",
                "max_restore_bytes_per_sec": "1024mb",
                "uri": "hdfs://foo.host:9000",
                "max_snapshot_bytes_per_sec": "1024mb",
            },
        }
        fake_es = MagicMock(return_value=MockElastic(ack=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert not elasticsearch8_module.repository_create("foo", body=body)

    def test_snapshot_create_repository_failure(self):
        """
        Test snapshot create repository with failure
        """
        body = {
            "type": "hdfs",
            "settings": {
                "path": "elastic_snapshots",
                "max_restore_bytes_per_sec": "1024mb",
                "uri": "hdfs://foo.host:9000",
                "max_snapshot_bytes_per_sec": "1024mb",
            },
        }
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.repository_create,
                name="foo",
                body=body,
            )

    def test_snapshot_cleanup_repository(self):
        """
        Test snapshot delete repository
        """
        expected = {"results": {"deleted_blobs": 0, "deleted_bytes": 0}}
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.repository_cleanup(name="foo") == expected

    def test_snapshot_cleanup_repository_not_found(self):
        """
        Test snapshot delete repository with false ack
        """
        fake_es = MagicMock(return_value=MockElastic(found=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.repository_cleanup("foo")

    def test_snapshot_cleanup_repository_failure(self):
        """
        Test snapshot delete repository with failure
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.repository_cleanup, name="foo"
            )

    def test_snapshot_delete_repository(self):
        """
        Test snapshot delete repository
        """
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.repository_delete(name="foo")

    def test_snapshot_delete_repository_not_found(self):
        """
        Test snapshot delete repository with false ack
        """
        fake_es = MagicMock(return_value=MockElastic(found=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.repository_delete("foo")

    def test_snapshot_delete_repository_failure(self):
        """
        Test snapshot delete repository with failure
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.repository_delete, name="foo"
            )

    def test_snapshot_verify_repository(self):
        """
        Test snapshot verify repository
        """
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.repository_verify(name="foo")

    def test_snapshot_verify_repository_not(self):
        """
        Test snapshot verify repository not found
        """
        fake_es = MagicMock(return_value=MockElastic(found=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert not elasticsearch8_module.repository_verify("foo")

    def test_snapshot_verify_repository_failure(self):
        """
        Test snapshot verify repository with failure
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.repository_verify, name="foo"
            )

    def test_snapshot_status(self):
        """
        Test snapshot status
        """
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.snapshot_status(repository="foo") == {"snapshots": []}

    def test_snapshot_status_failure(self):
        """
        Test snapshot status
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError, elasticsearch8_module.snapshot_status, repository="foo"
            )

    def test_snapshot_get(self):
        """
        Test snapshot get method
        """
        expected = {
            "snapshots": [{"snapshot": "foo", "uuid": "foo", "repository": "foo"}]
        }
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.snapshot_get(repository="foo", snapshot="foo") == expected

    def test_snapshot_get_not(self):
        """
        Test snapshot get method when snapshot not found
        """
        fake_es = MagicMock(return_value=MockElastic(found=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.snapshot_get,
                repository="foo",
                snapshot="foo",
            )

    def test_snapshot_get_failure(self):
        """
        Test snapshot get method when failure
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.snapshot_get,
                repository="foo",
                snapshot="foo",
            )

    def test_snapshot_create(self):
        """
        Test snapshot create method
        """
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.snapshot_create(repository="foo", snapshot="foo")

    def test_snapshot_create_not(self):
        """
        Test snapshot create method when snapshot not found
        """
        fake_es = MagicMock(return_value=MockElastic(accepted=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert not elasticsearch8_module.snapshot_create(repository="foo", snapshot="foo")

    def test_snapshot_create_failure(self):
        """
        Test snapshot create method when failure
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.snapshot_create,
                repository="foo",
                snapshot="foo",
            )

    def test_snapshot_clone(self):
        """
        Test snapshot create method
        """
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.snapshot_clone(repository="foo", snapshot="foo", target_snapshot="bar")

    def test_snapshot_clone_not(self):
        """
        Test snapshot create method when snapshot not found
        """
        fake_es = MagicMock(return_value=MockElastic(ack=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert not elasticsearch8_module.snapshot_clone(repository="foo", snapshot="foo", target_snapshot="bar")

    def test_snapshot_clone_failure(self):
        """
        Test snapshot create method when failure
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.snapshot_clone,
                repository="foo",
                snapshot="foo",
                target_snapshot="bar",
            )

    def test_snapshot_restore(self):
        """
        Test snapshot create method
        """
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.snapshot_restore(repository="foo", snapshot="foo")

    def test_snapshot_restore_not(self):
        """
        Test snapshot restore method when snapshot not found
        """
        fake_es = MagicMock(return_value=MockElastic(accepted=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert not elasticsearch8_module.snapshot_restore(repository="foo", snapshot="foo")

    def test_snapshot_restore_failure(self):
        """
        Test snapshot restore method when failure
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.snapshot_restore,
                repository="foo",
                snapshot="foo",
            )

    def test_snapshot_delete(self):
        """
        Test snapshot delete method
        """
        fake_es = MagicMock(return_value=MockElastic())
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.snapshot_delete(repository="foo", snapshot="foo")

    def test_snapshot_delete_not(self):
        """
        Test snapshot delete method when snapshot not found
        """
        fake_es = MagicMock(return_value=MockElastic(found=False))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            assert elasticsearch8_module.snapshot_delete(repository="foo", snapshot="foo")

    def test_snapshot_delete_failure(self):
        """
        Test snapshot delete method when failure
        """
        fake_es = MagicMock(return_value=MockElastic(failure=True))
        with patch.object(elasticsearch8_module, "_get_instance", fake_es):
            pytest.raises(
                CommandExecutionError,
                elasticsearch8_module.snapshot_delete,
                repository="foo",
                snapshot="foo",
            )

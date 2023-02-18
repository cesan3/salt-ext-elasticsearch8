"""
    :codeauthor: Cesar Sanchez <cesan3@gmail.com>
"""
import pytest

from elasticsearch import NotFoundError
from elasticsearch import TransportError
from elasticsearch import ApiError

class ApiResult:
    def __init__(self, meta, body):
        self.meta = meta
        self.body = body


def esversion(func):
    def wrapper(cls, **kwargs):
        result = func(cls, **kwargs)
        return ApiResult({}, result)

    return wrapper


class MockElasticIndices:
    """
    Mock of Elasticsearch IndicesClient
    """

    def __init__(
        self, found=True, failure=False, ack=True, shards=True, ack_shards=True
    ):
        self.found = found
        self.failure = failure
        self.ack = ack
        self.shards = shards
        self.ack_shards = ack_shards

    @esversion
    def put_alias(self, *args, **kwargs):
        """
        Mock of put_alias method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def delete_alias(self, *args, **kwargs):
        """
        Mock of delete_alias method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def exists_alias(self, *args, **kwargs):
        """
        Mock of exists_alias method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def get_alias(self, *args, **kwargs):
        """
        Mock of get_alias method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    @esversion
    def create(self, *args, **kwargs):
        """
        Mock of index method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        if self.shards:
            return {"acknowledged": self.ack, "shards_acknowledged": self.ack_shards}
        else:
            return {"acknowledged": self.ack}

    @esversion
    def delete(self, *args, **kwargs):
        """
        Mock of delete method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def exists(self, *args, **kwargs):
        """
        Mock of exists method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return True

    @esversion
    def get(self, *args, **kwargs):
        """
        Mock of get method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    @esversion
    def open(self, *args, **kwargs):
        """
        Mock of open method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def close(self, *args, **kwargs):
        """
        Mock of close method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def put_mapping(self, *args, **kwargs):
        """
        Mock of put_mapping method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def get_mapping(self, *args, **kwargs):
        """
        Mock of get_mapping method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    @esversion
    def put_template(self, *args, **kwargs):
        """
        Mock of put_template method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def delete_template(self, *args, **kwargs):
        """
        Mock of delete_template method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def exists_index_template(self, *args, **kwargs):
        """
        Mock of exists_template method
        """
        if not self.found:
            return False
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return True

    @esversion
    def exists_template(self, *args, **kwargs):
        """
        Mock of exists_template method
        """
        if not self.found:
            return False
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return True

    @esversion
    def get_template(self, *args, **kwargs):
        """
        Mock of get_template method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    @esversion
    def get_settings(self, *args, **kwargs):
        """
        Mock of get_settings method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"foo": "key"}

    @esversion
    def put_settings(self, **kwargs):
        """
        Mock of get_settings method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": True}

    @esversion
    def flush(self, hosts=None, profile=None, **kwargs):
        """
        Mock of flush method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"_shards": {"failed": 0, "successful": 0, "total": 0}}


class MockElasticCluster:
    """
    Mock of Elasticsearch ClusterClient
    """

    def __init__(self, failure=False):
        self.failure = failure

    @esversion
    def health(self, *args, **kwargs):
        """
        Mock of health method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return [{"test": "key"}]

    @esversion
    def stats(self, *args, **kwargs):
        """
        Mock of health method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return [{"test": "key"}]

    @esversion
    def get_settings(self, *args, **kwargs):
        """
        Mock of get_settings method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"transient": {}, "persistent": {}}

    @esversion
    def put_settings(self, *args, **kwargs):
        """
        Mock of put_settings method
        """
        result = {
            "acknowledged": True,
            "transient": {},
            "persistent": {"indices": {"recovery": {"max_bytes_per_sec": "50mb"}}},
        }
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return result

    @esversion
    def allocation_explain(self, *args, **kwargs):
        """
        Mock of allocation_explain method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"allocate_explanation": "foo", "can_allocate": "no"}

    @esversion
    def pending_tasks(self, *args, **kwargs):
        """
        Mock of pending tasks method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {}


class MockElasticNodes:
    """
    Mock of Elasticsearch NodesClient
    """

    def __init__(self, failure=False):
        self.failure = failure

    @esversion
    def info(self, *args, **kwargs):
        """
        Mock of info method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return [{"test": "key"}]


class MockElasticIndicesPass:
    pass


class MockElasticIngestPass:
    pass


class MockElasticIngest:
    """
    Mock of Elastic Ingest
    """

    def __init__(self, found=True, failure=False, ack=True):
        self.found = found
        self.failure = failure
        self.ack = ack

    @esversion
    def processor_grok(self, *args, **kwargs):
        """
        Mock of processor_grok method
        """
        expected = {"patterns": {}}
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return expected

    @esversion
    def geo_ip_stats(self, *args, **kwargs):
        """
        Mock of geo_ip_stats method
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
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return expected

    @esversion
    def get_pipeline(self, *args, **kwargs):
        """
        Mock of get_pipeline method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    @esversion
    def delete_pipeline(self, *args, **kwargs):
        """
        Mock of delete_pipeline method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def put_pipeline(self, *args, **kwargs):
        """
        Mock of delete_pipeline method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def simulate(self, *args, **kwargs):
        """
        Mock of simulate method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}


class MockElasticSnapshot:
    """
    Mock of elastic snapshot
    """

    def __init__(self, found=True, failure=False, ack=True, accepted=True):
        self.found = found
        self.failure = failure
        self.ack = ack
        self.accepted = accepted

    @esversion
    def get_repository(self, **kwargs):
        """
        Mock of get_repository method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        result = {
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
        return result

    @esversion
    def create_repository(self, **kwargs):
        """
        Mock of create repository method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def delete_repository(self, **kwargs):
        """
        Mock of delete repository method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def cleanup_repository(self, **kwargs):
        """
        Mock of cleanup repository method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"results": {"deleted_bytes": 0, "deleted_blobs": 0}}

    @esversion
    def verify_repository(self, **kwargs):
        """
        Mock of verify repository method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"nodes": {"foo": {"name": "node1"}, "bar": {"name": "node2"}}}

    @esversion
    def status(self, **kargs):
        """
        Mock of snapshot status method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"snapshots": []}

    @esversion
    def get(self, **kargs):
        """
        Mock of snapshot get method
        """
        if not self.found:
            # raise NotFoundError("not found error", {}, {})
            raise TransportError("customer error", (123, 0))
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"snapshots": [{"snapshot": "foo", "uuid": "foo", "repository": "foo"}]}

    @esversion
    def create(self, **kwargs):
        """
        Mock of snapshot create method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"accepted": self.accepted}

    @esversion
    def clone(self, **kwargs):
        """
        Mock of snapshot create method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def restore(self, **kwargs):
        """
        Mock of snapshot restore method
        """
        from collections import namedtuple

        _api_meta = namedtuple("api_error", "status")
        _meta = _api_meta(0)
        if self.failure:
            raise ApiError("error restoring snapshot", _meta, "")
        return {"accepted": self.accepted}

    @esversion
    def delete(self, **kwargs):
        """
        Mock of snapshot delete method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}


class MockElastic:
    """
    Mock of Elasticsearch client
    """

    def __init__(
        self,
        found=True,
        failure=False,
        accepted=True,
        ack=True,
        shards=True,
        ack_shards=True,
        no_indices=False,
        no_ingest=False,
    ):
        self.failure = failure
        self.found = found
        self.ack = ack
        self.nodes = MockElasticNodes(failure=failure)
        self.cluster = MockElasticCluster(failure=failure)
        self.snapshot = MockElasticSnapshot(
            found=found, failure=failure, ack=ack, accepted=accepted
        )
        if no_indices:
            self.indices = MockElasticIndicesPass()
        else:
            self.indices = MockElasticIndices(
                found=found,
                failure=failure,
                ack=ack,
                shards=shards,
                ack_shards=ack_shards,
            )
        if no_ingest:
            self.ingest = MockElasticIngestPass()
        else:
            self.ingest = MockElasticIngest(found=found, failure=failure, ack=ack)

    @esversion
    def info(self, *args, **kwargs):
        """
        Mock of info method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return [{"test": "key"}]

    @esversion
    def index(self, *args, **kwargs):
        """
        Mock of index method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    @esversion
    def delete(self, *args, **kwargs):
        """
        Mock of delete method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    @esversion
    def exists(self, *args, **kwargs):
        """
        Mock of exists method
        """
        if not self.found:
            return False
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return True

    @esversion
    def get(self, *args, **kwargs):
        """
        Mock of index method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    @esversion
    def get_script(self, *args, **kwargs):
        """
        Mock of get_script method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    @esversion
    def put_script(self, *args, **kwargs):
        """
        Mock of put_script method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    @esversion
    def delete_script(self, *args, **kwargs):
        """
        Mock of delete_template method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

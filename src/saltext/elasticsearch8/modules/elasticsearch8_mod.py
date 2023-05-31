"""
Salt execution module

Elasticsearch - A distributed RESTful search and analytics server for Elasticsearch 8
Module to provide Elasticsearch compatibility to Salt
(compatible with Elasticsearch version 8+).  Copied from elasticsearch.py module and updated.

.. versionadded:: 3005.1-4

:codeauthor: Cesar Sanchez <cesan3@gmail.com>

:depends: elasticsearch-py <http://elasticsearch-py.readthedocs.org/en/latest/>

:configuration: This module accepts connection configuration details either as
                parameters or as configuration settings in /etc/salt/minion on the relevant
                minions:

.. code-block:: yaml

    elasticsearch:
      host: '10.10.10.100:9200'

    elasticsearch-cluster:
      hosts:
        - '10.10.10.100:9200'
        - '10.10.10.101:9200'
        - '10.10.10.102:9200'

    elasticsearch-extra:
      hosts:
        - '10.10.10.100:9200'
      use_ssl: True
      verify_certs: True
      ca_certs: /path/to/custom_ca_bundle.pem
      number_of_shards: 1
      number_of_replicas: 0
      functions_blacklist:
        - 'saltutil.find_job'
        - 'pillar.items'
        - 'grains.items'

      proxies:
        - http: http://proxy:3128
        - https: http://proxy:1080

When specifying proxies the requests backend will be used and the 'proxies'
data structure is passed as-is to that module.

This data can also be passed into pillar. Options passed into opts will
overwrite options passed into pillar.

Some functionality might be limited by elasticsearch-py and Elasticsearch server versions.
"""
# pylint: disable=too-many-lines
import logging
import re

from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError

log = logging.getLogger(__name__)

try:
    import elasticsearch
    from elastic_transport import RequestsHttpNode
    ES_MAJOR_VERSION = elasticsearch.__version__[0]
    logging.getLogger("elasticsearch").setLevel(logging.CRITICAL)
    HAS_ELASTICSEARCH = True
except ImportError:
    HAS_ELASTICSEARCH = False

__virtualname__ = "elasticsearch"


def __virtual__():
    """
    Only load if elasticsearch librarielastic exist and ES version is 8+.
    """
    if not HAS_ELASTICSEARCH:
        return (
            False,
            "Cannot load module elasticsearch: elasticsearch librarielastic not found",
        )
    else:
        if ES_MAJOR_VERSION >= 8:
            return __virtualname__
        return (False, "Cannot load the module, elasticserach version is not 8")


def _get_instance(hosts=None, profile=None):
    """
    Return the elasticsearch instance
    """
    elastic = None
    proxies = None
    ca_certs = None
    verify_certs = True
    http_auth = None
    timeout = 10

    if profile is None:
        profile = "elasticsearch"

    if isinstance(profile, str):
        _profile = __salt__["config.option"](profile)
    elif isinstance(profile, dict):
        _profile = profile
    if _profile:
        hosts = _profile.get("host", hosts)
        if not hosts:
            hosts = _profile.get("hosts", hosts)
        proxies = _profile.get("proxies", None)
        ca_certs = _profile.get("ca_certs", None)
        verify_certs = _profile.get("verify_certs", True)
        username = _profile.get("username", None)
        password = _profile.get("password", None)
        timeout = _profile.get("timeout", 10)

        if username and password:
            http_auth = (username, password)

    if hosts is None:
        hosts = ["http://127.0.0.1:9200"]
    if isinstance(hosts, str):
        _re = re.compile(r"(http[s]*://)(.*)")
        match = _re.match(hosts)
        if match:
            (schema, hostport) = match.groups()
            (host, port) = hostport.split(":")
            if port is None:
                port = "9200"
            hosts = [f"{schema}{host}:{port}"]
        else:
            hosts = [hosts]
    try:
        if proxies:
            elastic = elasticsearch.Elasticsearch(
                hosts,
                ca_certs=ca_certs,
                verify_certs=verify_certs,
                http_auth=http_auth,
                request_timeout=timeout,
                node_class=RequestsHttpNode,
            )
        else:
            elastic = elasticsearch.Elasticsearch(
                hosts,
                ca_certs=ca_certs,
                verify_certs=verify_certs,
                http_auth=http_auth,
                request_timeout=timeout,
            )

        # Try the connection
        elastic.info()
    except elasticsearch.exceptions.TransportError as err:
        raise CommandExecutionError(
            f"Could not connect to Elasticsearch host/ cluster {hosts} due to {err.errors}"
        ) from err
    return elastic


def ping(
    hosts=None,
    profile=None,
    allow_failure=False,
):
    """
    .. versionadded:: 3005.1-4

    Test connection to Elasticsearch instance. This method does not fail if not explicitly specified.

    allow_failure
        Throw exception if ping fails

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.ping allow_failure=True
        salt myminion elasticsearch.ping profile=elasticsearch-extra
    """
    try:
        _get_instance(hosts=hosts, profile=profile)
    except CommandExecutionError:
        if allow_failure:
            raise
        return False
    return True


def info(
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    pretty=None,
):
    """
    .. versionadded:: 2017.7.0

    Return Elasticsearch information.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.info
        salt myminion elasticsearch.info profile=elasticsearch-extra
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    try:
        return elastic.info(error_trace=error_trace, filter_path=filter_path, human=human, pretty=pretty).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve server information, server returned errors {err.errors}"
        ) from err


def node_info(
    hosts=None,
    profile=None,
    node_id=None,
    metric=None,
    error_trace=None,
    filter_path=None,
    flat_settings=False,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    .. versionadded:: 3005.1-4

    Return Elasticsearch node information.

    node_id
        Comma-separated list of node IDs or namelastic used to limit returned
        information.
    metric
        Limits the information returned to the specific metrics. Supports
        a comma-separated list, such as http,ingest.
    flat_settings
        If true, returns settings in flat format.
    master_timeout
        Period to wait for a connection to the master node. If
        no response is received before the timeout expires, the request fails and
        returns an error.
    timeout
        Period to wait for a response. If no response is received before
        the timeout expires, the request fails and returns an error.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.node_info flat_settings=True
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.nodes.info(
            node_id=node_id,
            metric=metric,
            error_trace=error_trace,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve node information, server returned errors {err.errors}"
        ) from err


def cluster_health(
    index=None,
    level="cluster",
    local=False,
    hosts=None,
    profile=None,
    error_trace=None,
    expand_wildcards=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
    wait_for_active_shards=None,
    wait_for_events=None,
    wait_for_no_initializing_shards=None,
    wait_for_no_relocating_shards=None,
    wait_for_nodes=None,
    wait_for_status=None,
):
    """
    # pylint: disable=line-too-long

    .. versionadded:: 3005.1-4

    Return Elasticsearch cluster health.

    index
        Comma-separated list of data streams, indices, and index aliases
        used to limit the request. Wildcard expressions (*) are supported. To target
        all data streams and indices in a cluster, omit this parameter or use _all
        or '*'.
    expand_wildcards
        Whether to expand wildcard expression to concrete indices
        that are open, closed or both.
        Valuelastic can be 'all', 'closed', 'hidden', 'none', 'open'
    level
        Can be one of cluster, indices or shards. Controls the details
        level of the health information returned.
    local
        If true, the request retrievelastic information from the local node
        only. Defaults to false, which means information is retrieved from the master
        node.
    master_timeout
        Period to wait for a connection to the master node. If
        no response is received before the timeout expires, the request fails and
        returns an error.
    timeout
        Period to wait for a response. If no response is received before
        the timeout expires, the request fails and returns an error.
    wait_for_active_shards
        A number controlling to how many active shards
        to wait for, all to wait for all shards in the cluster to be active, or 0
        to not wait.
    wait_for_events
        Can be one of immediate, urgent, high, normal, low, languid.
        Wait until all currently queued events with the given priority are processed.
    wait_for_no_initializing_shards
        A boolean value which controls whether
        to wait (until the timeout provided) for the cluster to have no shard initializations.
        Defaults to false, which means it will not wait for initializing shards.
    wait_for_no_relocating_shards
        A boolean value which controls whether
        to wait (until the timeout provided) for the cluster to have no shard relocations.
        Defaults to false, which means it will not wait for relocating shards.
    wait_for_nodes
        The request waits until the specified number N of nodes
        is available. It also accepts >=N, <=N, >N and <N. Alternatively, it is possible
        to use ge(N), le(N), gt(N) and lt(N) notation.
    wait_for_status
        One of green, yellow or red. Will wait (until the timeout
        provided) until the status of the cluster changelastic to the one provided or
        better, i.e. green > yellow > red. By default, will not wait for any status.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.cluster_health
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.cluster.health(
            index=index,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            filter_path=filter_path,
            human=human,
            level=level,
            local=local,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
            wait_for_active_shards=wait_for_active_shards,
            wait_for_events=wait_for_events,
            wait_for_no_initializing_shards=wait_for_no_initializing_shards,
            wait_for_no_relocating_shards=wait_for_no_relocating_shards,
            wait_for_nodes=wait_for_nodes,
            wait_for_status=wait_for_status,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve health information, server returned errors {err.errors}"
        ) from err


def cluster_allocation_explain(
    hosts=None,
    profile=None,
    current_node=None,
    error_trace=None,
    filter_path=None,
    human=None,
    include_disk_info=None,
    include_yes_decisions=None,
    index=None,
    pretty=None,
    primary=None,
    shard=None,
):
    """
    .. versionadded:: 3005.1-4

    Return Elasticsearch cluster allocation explain

    current_node
        Specifielastic the node ID or the name of the node to only explain
        a shard that is currently located on the specified node.
    include_disk_info
        If true, returns information about disk usage and shard
        sizelastic.
    include_yes_decisions
        If true, returns YES decisions in explanation.
    index
        Specifielastic the name of the index that you would like an explanation
        for.
    primary
        If true, returns explanation for the primary shard for the given
        shard ID.
    shard
        Specifielastic the ID of the shard that you would like an explanation
        for.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.cluster_allocation_explain
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.cluster.allocation_explain(
            current_node=current_node,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            include_disk_info=include_disk_info,
            include_yes_decisions=include_yes_decisions,
            index=index,
            pretty=pretty,
            primary=primary,
            shard=shard,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve cluster allocation explanation, server returned errors {err.errors}"
        ) from err


def cluster_pending_tasks(
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    local=None,
    master_timeout=None,
    pretty=None,
):
    """
    .. versionadded:: 3005.1-4

    Returns a list of any cluster-level changelastic (e.g. create index, update mapping,
    allocate or fail shard) which have not yet been executed.


    local
        Return local information, do not retrieve the state from master
        node (default: false)
    master_timeout
        Specify timeout for connection to master

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.cluster_pending_tasks
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.cluster.pending_tasks(
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            local=local,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve cluster allocation explanation, server returned errors {err.errors}"
        ) from err


def cluster_stats(
    node_id=None,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    flat_settings=None,
    human=None,
    pretty=None,
    timeout=None,
):
    """
    .. versionadded:: 3005.1-4

    Return Elasticsearch cluster stats.

    node_id
        Comma-separated list of node filters used to limit returned information.
        Defaults to all nodes in the cluster.
    flat_settings
        Return settings in flat format (default: false)
    timeout
        Period to wait for each node to respond. If a node does not respond
        before its timeout expires, the response does not include its stats. However,
        timed out nodes are included in the response’s _nodes.failed property. Defaults
        to no timeout.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.cluster_stats
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.cluster.stats(
            node_id=node_id,
            error_trace=error_trace,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            pretty=pretty,
            timeout=timeout,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve cluster stats, server returned errors {err.errors}"
        ) from err


def cluster_get_settings(
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    flat_settings=False,
    human=None,
    include_defaults=False,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    .. versionadded:: 3005.1-4

    Return Elasticsearch cluster settings.

    flat_settings
        Return settings in flat format (default: false)
    include_defaults
        Whether to return all default clusters setting.
    master_timeout
        Explicit operation timeout for connection to master node
    timeout
        Explicit operation timeout

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.cluster_get_settings
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.cluster.get_settings(
            error_trace=error_trace,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            include_defaults=include_defaults,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve cluster settings, server returned errors {err.errors}"
        ) from err


def cluster_put_settings(
    body=None,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    flat_settings=False,
    human=None,
    master_timeout=None,
    persistent=None,
    pretty=None,
    timeout=None,
    transient=None,
):
    """
    # pylint: disable=line-too-long
    .. versionadded:: 3000

    Set Elasticsearch cluster settings.

    body
        The settings to be updated. Can be either 'transient' or 'persistent' (survives cluster restart)
        http://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-update-settings.html

    flat_settings
        Return settings in flat format.

    CLI Example:

    .. code-block:: bash

      salt myminion elasticsearch.cluster_put_settings '{"persistent": {"indices.recovery.max_bytes_per_sec": "50mb"}}'
      salt myminion elasticsearch.cluster_put_settings '{"transient": {"indices.recovery.max_bytes_per_sec": "50mb"}}'
    """
    if body is None and persistent is None and transient is None:
        message = "You must provide a body with settings or provide the persistent or transient data"
        raise SaltInvocationError(message)
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        if body is not None:
            return elastic.cluster.put_settings(
                body=body,
                flat_settings=flat_settings,
                error_trace=error_trace,
                filter_path=filter_path,
                human=human,
                master_timeout=master_timeout,
                pretty=pretty,
                timeout=timeout,
            ).body
        else:
            return elastic.cluster.put_settings(
            flat_settings=flat_settings,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
            transient=transient,
            persistent=persistent,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot update cluster settings, server returned errors {err.errors}"
        ) from err


def alias_create(
    indices,
    alias,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_=None,
    filter_path=None,
    human=None,
    index_routing=None,
    is_write_index=None,
    master_timeout=None,
    pretty=None,
    routing=None,
    search_routing=None,
    timeout=None,
):
    """
    Create an alias for a specific index/indices

    indices
        A comma-separated list of index namelastic the alias should point to
        (supports wildcards); use _all to perform the operation on all indices.
    alias
        The name of the alias to be created or updated

    filter
        Filter definittion
    index_routing
        index_routing
    is_write_index
        is_write_index
    master_timeout
        Specify timeout for connection to master
    routing
        Routing definition
    search_routing
        search_routing
    timeout
        Explicit timestamp for the document

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.alias_create testindex_v1 testindex
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    try:
        result = elastic.indices.put_alias(
            index=indices,
            name=alias,
            error_trace=error_trace,
            filter=filter_,
            filter_path=filter_path,
            human=human,
            index_routing=index_routing,
            is_write_index=is_write_index,
            master_timeout=master_timeout,
            pretty=pretty,
            routing=routing,
            search_routing=search_routing,
            timeout=timeout,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot create alias {alias} in index {indices}, server returned errors {err.errors}"
        ) from err


def alias_delete(
    indices,
    aliases,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    Delete an alias of an index

    indices
        Single or multiple indices separated by comma, use _all to perform the operation on all indices.
    aliases
        Alias namelastic separated by comma

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.alias_delete testindex_v1 testindex
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    try:
        result = elastic.indices.delete_alias(
            index=indices,
            name=aliases,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.exceptions.NotFoundError:
        return True
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot delete alias {aliases} in index {indices}, server returned errors {err.errors}"
        ) from err


def alias_exists(
    aliases,
    indices=None,
    hosts=None,
    profile=None,
    allow_no_indices=None,
    error_trace=None,
    expand_wildcards=None,
    filter_path=None,
    human=None,
    ignore_unavailable=None,
    local=None,
    pretty=None,
):
    """
    Return a boolean indicating whether given alias exists

    indices
        A comma-separated list of index namelastic to filter aliases
    aliases
        A comma-separated list of alias namelastic to return
    allow_no_indices
        Whether to ignore if a wildcard indices expression resolves
        into no concrete indices. (This includelastic _all string or when no indices
        have been specified)
    expand_wildcards
        Whether to expand wildcard expression to concrete indices
        that are open, closed or both.
        Valid valuelastic are 'all', 'closed', 'hidden', 'none', 'open'
    ignore_unavailable
        Whether specified concrete indices should be ignored
        when unavailable (missing or closed)
    local
        Return local information, do not retrieve the state from master
        node (default: false)

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.alias_exists None testindex
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    try:
        return elastic.indices.exists_alias(
            name=aliases,
            index=indices,
            allow_no_indices=allow_no_indices,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            filter_path=filter_path,
            human=human,
            ignore_unavailable=ignore_unavailable,
            local=local,
            pretty=pretty,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return False
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot get alias {aliases} in index {indices}, server returned errors {err.errors}"
        ) from err


def alias_get(
    aliases,
    indices=None,
    hosts=None,
    profile=None,
    allow_no_indices=None,
    error_trace=None,
    expand_wildcards=None,
    filter_path=None,
    human=None,
    ignore_unavailable=None,
    local=None,
    pretty=None,
):
    """
    Check for the existence of an alias and if it exists, return it

    indices
        A comma-separated list of index namelastic to filter aliases
    aliases
        A comma-separated list of alias namelastic to return
    allow_no_indices
        Whether to ignore if a wildcard indices expression resolves
        into no concrete indices. (This includelastic _all string or when no indices
        have been specified)
    expand_wildcards
        Whether to expand wildcard expression to concrete indices
        that are open, closed or both.
        Valid valuelastic are 'all', 'closed', 'hidden', 'none', 'open'
    ignore_unavailable
        Whether specified concrete indices should be ignored
        when unavailable (missing or closed)
    local
        Return local information, do not retrieve the state from master
        node (default: false)

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.alias_get testindex
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.indices.get_alias(
            index=indices,
            name=aliases,
            allow_no_indices=allow_no_indices,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            filter_path=filter_path,
            human=human,
            ignore_unavailable=ignore_unavailable,
            local=local,
            pretty=pretty,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot get alias {aliases} in index {indices}, server returned errors {err.errors}"
        ) from err


def document_create(
    index,
    body=None,
    hosts=None,
    profile=None,
    source=None,
    document=None,
    id_=None,
    error_trace=None,
    filter_path=None,
    human=None,
    if_primary_term=None,
    if_seq_no=None,
    op_type=None,
    pipeline=None,
    pretty=None,
    refresh=None,
    require_alias=None,
    routing=None,
    timeout=None,
    version=None,
    version_type=None,
    wait_for_active_shards=None,
):
    """
    Create a document in a specified index

    index
        Index name where the document should reside
    body
        Document to store
    source
        URL of file specifying document to store. Cannot be used in combination with body.
    document
        Document to store. If body doesn't exist, this is the dictionary with the document contents
    if_primary_term
        only perform the index operation if the last operation
        that has changed the document has the specified primary term
    if_seq_no
        only perform the index operation if the last operation that
        has changed the document has the specified sequence number
    op_type
        Explicit operation type. Defaults to index for requests with
        an explicit document ID, and to createfor requests without an explicit
        document ID
    pipeline
        The pipeline id to preprocess incoming documents with
    refresh
        If true then refresh the affected shards to make this operation
        visible to search, if wait_for then wait for a refresh to make this operation
        visible to search, if false (the default) then do nothing with refreshelastic.
    require_alias
        When true, requirelastic destination to be an alias. Default
        is false
    routing
        Specific routing value
    timeout
        Explicit operation timeout
    version
        Explicit version number for concurrency control
    version_type
        Specific version type
    wait_for_active_shards
        Sets the number of shard copielastic that must be active
        before proceeding with the index operation. Defaults to 1, meaning the primary
        shard only. Set to all for all shard copies, otherwise set to any non-negative
        value less than or equal to the total number of copielastic for the shard (number
        of replicas + 1)

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.document_create testindex doctype1 '{}'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    if source and body:
        message = "Either body or source should be specified but not both."
        raise SaltInvocationError(message)
    if source:
        body = __salt__["cp.get_file_str"](source, saltenv=__opts__.get("saltenv", "base"))
    try:
        if body is not None:
            return elastic.index(
                index=index,
                document=body,
                id=id_,
                error_trace=error_trace,
                filter_path=filter_path,
                human=human,
                if_primary_term=if_primary_term,
                if_seq_no=if_seq_no,
                op_type=op_type,
                pipeline=pipeline,
                pretty=pretty,
                refresh=refresh,
                require_alias=require_alias,
                routing=routing,
                timeout=timeout,
                version=version,
                version_type=version_type,
                wait_for_active_shards=wait_for_active_shards,
            ).body
        else:
            return elastic.index(
                index=index,
                document=document,
                id=id_,
                error_trace=error_trace,
                filter_path=filter_path,
                human=human,
                if_primary_term=if_primary_term,
                if_seq_no=if_seq_no,
                op_type=op_type,
                pipeline=pipeline,
                pretty=pretty,
                refresh=refresh,
                require_alias=require_alias,
                routing=routing,
                timeout=timeout,
                version=version,
                version_type=version_type,
                wait_for_active_shards=wait_for_active_shards,
            ).body

    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot create document in index {index}, server returned errors {err.errors}"
        ) from err


def document_delete(
    index,
    id_,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    if_primary_term=None,
    if_seq_no=None,
    pretty=None,
    refresh=None,
    routing=None,
    timeout=None,
    version=None,
    version_type=None,
    wait_for_active_shards=None,
):
    """
    Delete a document from an index

    index
        The name of the index
    if_primary_term
        only perform the delete operation if the last operation
        that has changed the document has the specified primary term
    if_seq_no
        only perform the delete operation if the last operation that
        has changed the document has the specified sequence number
    refresh
        If true then refresh the affected shards to make this operation
        visible to search, if wait_for then wait for a refresh to make this operation
        visible to search, if false (the default) then do nothing with refreshelastic.
    routing
        Specific routing value
    timeout
        Explicit operation timeout
    version
        Explicit version number for concurrency control
    version_type
        Specific version type
    wait_for_active_shards
        Sets the number of shard copielastic that must be active
        before proceeding with the delete operation. Defaults to 1, meaning the primary
        shard only. Set to all for all shard copies, otherwise set to any non-negative
        value less than or equal to the total number of copielastic for the shard (number
        of replicas + 1)

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.document_delete testindex doctype1 AUx-384m0Bug_8U80wQZ
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.delete(
            index=index,
            id=id_,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            if_primary_term=if_primary_term,
            if_seq_no=if_seq_no,
            pretty=pretty,
            refresh=refresh,
            routing=routing,
            timeout=timeout,
            version=version,
            version_type=version_type,
            wait_for_active_shards=wait_for_active_shards,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot delete document {id} in index {index}, server returned errors {err.errors}"
        ) from err


def document_exists(
    index,
    id_,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    preference=None,
    pretty=None,
    realtime=None,
    refresh=None,
    routing=None,
    source=None,
    source_excludes=None,
    source_includes=None,
    stored_fields=None,
    version=None,
    version_type=None,
):
    """
    Return a boolean indicating whether given document exists

    index
        The name of the index
    preference
        Specify the node or shard the operation should be performed
        on (default: random)
    realtime
        Specify whether to perform the operation in realtime or search
        mode
    refresh
        Refresh the shard containing the document before performing the
        operation
    routing
        Specific routing value
    source
        True or false to return the _source field or not, or a list of
        fields to return
    source_excludes
        A list of fields to exclude from the returned _source
        field
    source_includes
        A list of fields to extract and return from the _source
        field
    stored_fields
        A comma-separated list of stored fields to return in the
        response
    version
        Explicit version number for concurrency control
    version_type
        Specific version type.  version_type must be one of
        ('external', 'external_gte', 'force', 'internal')

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.document_exists testindex AUx-384m0Bug_8U80wQZ
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.exists(
            index=index,
            id=id_,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            preference=preference,
            pretty=pretty,
            realtime=realtime,
            refresh=refresh,
            routing=routing,
            source=source,
            source_excludes=source_excludes,
            source_includes=source_includes,
            stored_fields=stored_fields,
            version=version,
            version_type=version_type,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return False
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve document {id} from index {index}, server returned errors {err.errors}"
        ) from err


def document_get(
    index,
    id_,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    preference=None,
    pretty=None,
    realtime=None,
    refresh=None,
    routing=None,
    source=None,
    source_excludes=None,
    source_includes=None,
    stored_fields=None,
    version=None,
    version_type=None,
):
    """
    Check for the existence of a document and if it exists, return it

    index
        Index name where the document resides
    doc_type
        Type of the document, use _all to fetch the first document matching the ID across all types

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.document_get testindex AUx-384m0Bug_8U80wQZ
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.get(
            index=index,
            id=id_,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            preference=preference,
            pretty=pretty,
            realtime=realtime,
            refresh=refresh,
            routing=routing,
            source=source,
            source_excludes=source_excludes,
            source_includes=source_includes,
            stored_fields=stored_fields,
            version=version,
            version_type=version_type,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve document {id} from index {index}, server returned errors {err.errors}"
        ) from err


def index_create(
    index,
    hosts=None,
    profile=None,
    source=None,
    aliases=None,
    error_trace=None,
    filter_path=None,
    human=None,
    mappings=None,
    master_timeout=None,
    pretty=None,
    settings=None,
    timeout=None,
    wait_for_active_shards=None,
):
    """
    # pylint: disable=line-too-long
    Create an index

    index
        Index name
    source
        URL to file specifying index definition. Cannot be used in combination with body.
    index
        The name of the index
    aliases
        The list of aliases
    mappings
        Mapping for fields in the index. If specified, this mapping
        can include: - Field namelastic - Field data types - Mapping parameters
    master_timeout
        Specify timeout for connection to master
    settings
        Settings
    timeout
        Explicit operation timeout
    wait_for_active_shards
        Set the number of active shards to wait for before
        the operation returns. It also accepts ('all', 'index-setting')

    CLI Example:

    .. code-block:: bash

     salt myminion elasticsearch.index_create testindex
     salt myminion elasticsearch.index_create testindex2 \
        '{"settings" : {"index" : {"number_of_shards" : 3, "number_of_replicas" : 2}}}'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    if source and (settings or mappings):
        message = "Either (settings or mappings) or source should be specified but not both."
        raise SaltInvocationError(message)

    src_map = None
    if source:
        src_map = __salt__["cp.get_file_str"](source, saltenv=__opts__.get("saltenv", "base"))
    try:
        if src_map is not None:
            settings = src_map.get("settings")
            mappings = src_map.get("mappings")

        result = elastic.indices.create(
            index=index,
            aliases=aliases,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            mappings=mappings,
            master_timeout=master_timeout,
            pretty=pretty,
            settings=settings,
            timeout=timeout,
            wait_for_active_shards=wait_for_active_shards,
        ).body
        return result.get("acknowledged", False) and result.get("shards_acknowledged", True)
    except elasticsearch.TransportError as err:
        if "index_already_exists_exception" in err.errors:
            return True
        raise CommandExecutionError(
            f"Cannot create index {index}, server returned errors {err.errors}"
        ) from err


def index_delete(
    index,
    hosts=None,
    profile=None,
    allow_no_indices=None,
    error_trace=None,
    expand_wildcards=None,
    filter_path=None,
    human=None,
    ignore_unavailable=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    Delete an index

    index
        A comma-separated list of indices to delete; use _all or *
        string to delete all indices
    allow_no_indices
        Ignore if a wildcard expression resolvelastic to no concrete
        indices (default: false)
    expand_wildcards
        Whether wildcard expressions should get expanded to
        open, closed, or hidden indices.
        Accetps: ('all', 'closed', 'hidden', 'none', 'open')
    ignore_unavailable
        Ignore unavailable indexelastic (default: false)
    master_timeout
        Specify timeout for connection to master
    timeout
        Explicit operation timeout

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_delete testindex
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        result = elastic.indices.delete(
            index=index,
            allow_no_indices=allow_no_indices,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            filter_path=filter_path,
            human=human,
            ignore_unavailable=ignore_unavailable,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.exceptions.NotFoundError:
        return True
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot delete index {index}, server returned errors {err.errors}"
        ) from err


def index_exists(
    index,
    hosts=None,
    profile=None,
    allow_no_indices=None,
    error_trace=None,
    expand_wildcards=None,
    filter_path=None,
    flat_settings=False,
    human=None,
    ignore_unavailable=False,
    include_defaults=False,
    local=False,
    pretty=None,
):
    """
    Return a boolean indicating whether given index exists

    index
        A comma-separated list of index names
    allow_no_indices
        Ignore if a wildcard expression resolvelastic to no concrete
        indices (default: false)
    expand_wildcards
        Whether wildcard expressions should get expanded to
        open or closed indices (default: open)
        Accepts values: ('all', 'closed', 'hidden', 'none', 'open')
    flat_settings
        Return settings in flat format (default: false)
    ignore_unavailable
        Ignore unavailable indexelastic (default: false)
    include_defaults
        Whether to return all default setting for each of the
        indices.
    local
        Return local information, do not retrieve the state from master
        node (default: false)

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_exists testindex
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.indices.exists(
            index=index,
            allow_no_indices=allow_no_indices,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            ignore_unavailable=ignore_unavailable,
            include_defaults=include_defaults,
            local=local,
            pretty=pretty,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return False
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve index {index}, server returned errors {err.errors}"
        ) from err


def index_get(
    index,
    hosts=None,
    profile=None,
    allow_no_indices=None,
    error_trace=None,
    expand_wildcards=None,
    features=None,
    filter_path=None,
    flat_settings=False,
    human=None,
    ignore_unavailable=None,
    include_defaults=False,
    local=False,
    master_timeout=None,
    pretty=None,
):
    """
    Returns information about one or more indices.

    index
        Comma-separated list of data streams, indices, and index aliases
        used to limit the request. Wildcard expressions (*) are supported.
    allow_no_indices
        If false, the request returns an error if any wildcard
        expression, index alias, or _all value targets only missing or closed indices.
        This behavior applielastic even if the request targets other open indices. For
        example, a request targeting foo*,bar* returns an error if an index starts
        with foo but no index starts with bar.
    expand_wildcards
        Type of index that wildcard expressions can match. If
        the request can target data streams, this argument determinelastic whether wildcard
        expressions match hidden data streams. Supports comma-separated values, such
        as 'all', 'closed', 'hidden', 'none', 'open'
    features
        Return only information on specified index featurelastic.
        Support valuelastic such as 'aliases', 'mappings', 'settings'
    flat_settings
        If true, returns settings in flat format.
    ignore_unavailable
        If false, requests that target a missing index return
        an error.
    include_defaults
        If true, return all default settings in the response.
    local
        If true, the request retrievelastic information from the local node
        only. Defaults to false, which means information is retrieved from the master
        node.
    master_timeout
        Period to wait for a connection to the master node. If
        no response is received before the timeout expires, the request fails and
        returns an error.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_get testindex
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.indices.get(
            index=index,
            allow_no_indices=allow_no_indices,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            features=features,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            ignore_unavailable=ignore_unavailable,
            include_defaults=include_defaults,
            local=local,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve index {index}, server returned errors {err.errors}"
        ) from err


def index_open(
    index,
    allow_no_indices=True,
    expand_wildcards="closed",
    ignore_unavailable=True,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
    wait_for_active_shards=None,
):
    """
    .. versionadded:: 3005.1-4

    Open specified index.

    index
        A comma separated list of indices to open
    allow_no_indices
        Whether to ignore if a wildcard indices expression resolves
        into no concrete indices. (This includelastic _all string or when no indices
        have been specified)
    expand_wildcards
        Whether to expand wildcard expression to concrete indices
        that are open, closed or both.
        Valid choicelastic are ('all', 'closed', 'hidden', 'none', 'open')
    ignore_unavailable
        Whether specified concrete indices should be ignored
        when unavailable (missing or closed)
    master_timeout
        Specify timeout for connection to master
    timeout
        Explicit operation timeout
    wait_for_active_shards
        Sets the number of active shards to wait for before
        the operation returns. Valid choicelastic are an integer or 'all', 'index-setting' strings

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_open testindex
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        result = elastic.indices.open(
            index=index,
            allow_no_indices=allow_no_indices,
            expand_wildcards=expand_wildcards,
            ignore_unavailable=ignore_unavailable,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
            wait_for_active_shards=wait_for_active_shards,
        ).body

        return result.get("acknowledged", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot open index {index}, server returned errors {err.errors}"
        ) from err


def index_close(
    index,
    allow_no_indices=True,
    expand_wildcards="open",
    ignore_unavailable=True,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
    wait_for_active_shards=None,
):
    """
    .. versionadded:: 2017.7.0

    Close specified index.

    index
        A comma separated list of indices to close
    allow_no_indices
        Whether to ignore if a wildcard indices expression resolves
        into no concrete indices. (This includelastic _all string or when no indices
        have been specified)
    expand_wildcards
        Whether to expand wildcard expression to concrete indices
        that are open, closed or both.
        Valid choicelastic are ('all', 'closed', 'hidden', 'none', 'open')
    ignore_unavailable
        Whether specified concrete indices should be ignored
        when unavailable (missing or closed)
    master_timeout
        Specify timeout for connection to master
    timeout
        Explicit operation timeout
    wait_for_active_shards
        Sets the number of active shards to wait for before
        the operation returns. Valid choicelastic are an integer or 'all', 'index-setting' strings

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_close testindex
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        result = elastic.indices.close(
            index=index,
            allow_no_indices=allow_no_indices,
            expand_wildcards=expand_wildcards,
            ignore_unavailable=ignore_unavailable,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
            wait_for_active_shards=wait_for_active_shards,
        ).body

        return result.get("acknowledged", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot close index {index}, server returned errors {err.errors}"
        ) from err


def index_get_settings(
    hosts=None,
    profile=None,
    index=None,
    name=None,
    allow_no_indices=None,
    error_trace=None,
    expand_wildcards=None,
    filter_path=None,
    flat_settings=None,
    human=None,
    ignore_unavailable=None,
    include_defaults=None,
    local=None,
    master_timeout=None,
    pretty=None,
):
    """
    # pylint: disable=line-too-long
    .. versionadded:: 3000

    Check for the existence of an index and if it exists, return its settings
    http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-get-settings.html

    index
        (Optional, string) A comma-separated list of index names;
        use _all or empty string for all indices. Defaults to '_all'.
    name
        (Optional, string) The name of the settings that should be included
    allow_no_indices
        (Optional, boolean) Whether to ignore if a wildcard indices expression resolves into no concrete indices.
        (This includelastic _all string or when no indices have been specified)
    expand_wildcards
        (Optional, string) Whether to expand wildcard expression to concrete indices that are open, closed or both.
        Valid choicelastic are: open closed, none, all, hidden
    flat_settings
        (Optional, boolean) Return settings in flat format
    ignore_unavailable
        (Optional, boolean) Whether specified concrete indices should be ignored when unavailable (missing or closed)
    include_defaults
        (Optional, boolean) Whether to return all default setting for each of the indices.
    local
        (Optional, boolean) Return local information, do not retrieve the state from master node

    The defaults settings for the above parameters depend on the API version being used.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_get_settings index=testindex
    """

    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.indices.get_settings(
            index=index,
            name=name,
            allow_no_indices=allow_no_indices,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            ignore_unavailable=ignore_unavailable,
            include_defaults=include_defaults,
            local=local,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve index settings, server returned errors {err.errors}"
        ) from err


def index_put_settings(
    hosts=None,
    profile=None,
    source=None,
    settings=None,
    index=None,
    allow_no_indices=None,
    error_trace=None,
    expand_wildcards=None,
    filter_path=None,
    flat_settings=None,
    human=None,
    ignore_unavailable=None,
    master_timeout=None,
    preserve_existing=None,
    pretty=None,
    timeout=None,
):
    """
    # pylint: disable=line-too-long
    .. versionadded:: 3000

    Update existing index settings
    https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-update-settings.html

    source
        URL to file specifying index definition. Cannot be used in combination with body.
    settings:
        The index settings to be updated
    index
        A comma-separated list of index names; use _all or empty string
        to perform the operation on all indices
    allow_no_indices
        Whether to ignore if a wildcard indices expression resolves
        into no concrete indices. (This includelastic _all string or when no indices
        have been specified)
    expand_wildcards
        Whether to expand wildcard expression to concrete indices
        that are open, closed or both.
        Valuelastic can be 'all', 'closed', 'hidden', 'none', 'open'
    flat_settings
        Return settings in flat format (default: false)
    ignore_unavailable
        Whether specified concrete indices should be ignored
        when unavailable (missing or closed)
    master_timeout
        Specify timeout for connection to master
    preserve_existing
        Whether to update existing settings. If set to true
        existing settings on an index remain unchanged, the default is false
    timeout
        Explicit operation timeout

    The defaults settings for the above parameters depend on the API version being used.

    .. note::
        Elasticsearch time units can be found here:

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_put_settings index=testindex
          body='{"settings" : {"index" : {"number_of_replicas" : 2}}}'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    if source and settings:
        message = "Either settings or source should be specified but not both."
        raise SaltInvocationError(message)

    src_map = {}
    if source:
        src_map = __salt__["cp.get_file_str"](source, saltenv=__opts__.get("saltenv", "base"))
        settings = src_map.get("settings", settings)
    try:
        result = elastic.indices.put_settings(
            settings=settings,
            index=index,
            allow_no_indices=allow_no_indices,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            ignore_unavailable=ignore_unavailable,
            master_timeout=master_timeout,
            preserve_existing=preserve_existing,
            pretty=pretty,
            timeout=timeout,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.exceptions.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot update index settings, server returned errors {err.errors}"
        ) from err


def mapping_create(
    index,
    hosts=None,
    profile=None,
    source=None,
    allow_no_indices=None,
    date_detection=None,
    dynamic=None,
    dynamic_date_formats=None,
    dynamic_templates=None,
    error_trace=None,
    expand_wildcards=None,
    field_names=None,
    filter_path=None,
    human=None,
    ignore_unavailable=None,
    master_timeout=None,
    meta=None,
    numeric_detection=None,
    pretty=None,
    properties=None,
    routing=None,
    runtime=None,
    source_=None,
    timeout=None,
    write_index_only=None,
):
    """
    # pylint: disable=line-too-long
    Create a mapping in a given index

    index
        A comma-separated list of index namelastic the mapping should be added
        to (supports wildcards); use _all or omit to add the mapping on all indices.
    source
        URL to file specifying mapping definition. Cannot be used in combination with body.
    allow_no_indices
        Whether to ignore if a wildcard indices expression resolves
        into no concrete indices. (This includelastic _all string or when no indices
        have been specified)
    date_detection
        Controls whether dynamic date detection is enabled.
    dynamic
        Controls whether new fields are added dynamically.
    dynamic_date_formats
        If date detection is enabled then new string fields
        are checked against 'dynamic_date_formats' and if the value matchelastic then
        a new date field is added instead of string.
    dynamic_templates
        Specify dynamic templatelastic for the mapping.
    expand_wildcards
        Whether to expand wildcard expression to concrete indices
        that are open, closed or both.
    field_names
        Control whether field namelastic are enabled for the index.
    ignore_unavailable
        Whether specified concrete indices should be ignored
        when unavailable (missing or closed)
    master_timeout
        Specify timeout for connection to master
    meta
        A mapping type can have custom meta data associated with it. These
        are not used at all by Elasticsearch, but can be used to store application-specific
        metadata.
    numeric_detection
        Automatically map strings into numeric data typelastic for
        all fields.
    properties
        Mapping for a field. For new fields, this mapping can include:
        - Field name - Field data type - Mapping parameters
    routing
        Enable making a routing value required on indexed documents.
    runtime
        Mapping of runtime fields for the index.
    `source_`
        Control whether the _source field is enabled on the index.
    timeout
        Explicit operation timeout
    write_index_only
        When true, applielastic mappings only to the write index
        of an alias or data stream

    CLI Example:

    .. code-block:: bash

     salt myminion elasticsearch.mapping_create testindex user \
       '{ "user" : { "properties" : { "message" : {"type" : "string", "store" : true } } } }'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    if source and properties:
        message = "Either properties or source should be specified but not both."
        raise SaltInvocationError(message)

    src_map = {}
    if source:
        src_map = __salt__["cp.get_file_str"](source, saltenv=__opts__.get("saltenv", "base"))
        properties = src_map.get("properties", properties)
    try:
        result = elastic.indices.put_mapping(
            index=index,
            allow_no_indices=allow_no_indices,
            date_detection=date_detection,
            dynamic=dynamic,
            dynamic_date_formats=dynamic_date_formats,
            dynamic_templates=dynamic_templates,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            field_names=field_names,
            filter_path=filter_path,
            human=human,
            ignore_unavailable=ignore_unavailable,
            master_timeout=master_timeout,
            meta=meta,
            numeric_detection=numeric_detection,
            pretty=pretty,
            properties=properties,
            routing=routing,
            runtime=runtime,
            source=source_,
            timeout=timeout,
            write_index_only=write_index_only,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot create mapping {index}, server returned errors {err.errors}"
        ) from err


def mapping_get(
    index,
    hosts=None,
    profile=None,
    allow_no_indices=None,
    error_trace=None,
    expand_wildcards=None,
    filter_path=None,
    human=None,
    ignore_unavailable=None,
    local=None,
    master_timeout=None,
    pretty=None,
):
    """
    Retrieve mapping definition of index

    index
        A comma-separated list of index names
    allow_no_indices
        Whether to ignore if a wildcard indices expression resolves
        into no concrete indices. (This includelastic _all string or when no indices
        have been specified)
    expand_wildcards
        Whether to expand wildcard expression to concrete indices
        that are open, closed or both.
    ignore_unavailable
        Whether specified concrete indices should be ignored
        when unavailable (missing or closed)
    local
        Return local information, do not retrieve the state from master
        node (default: false)
    master_timeout
        Specify timeout for connection to master

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.mapping_get testindex user
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.indices.get_mapping(
            index=index,
            allow_no_indices=allow_no_indices,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            filter_path=filter_path,
            human=human,
            ignore_unavailable=ignore_unavailable,
            local=local,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve mapping {index}, server returned errors {err.errors}"
        ) from err


def index_template_create(
    name,
    hosts=None,
    profile=None,
    source=None,
    aliases=None,
    create=None,
    error_trace=None,
    filter_path=None,
    flat_settings=False,
    human=None,
    index_patterns=None,
    mappings=None,
    master_timeout=None,
    order=None,
    pretty=None,
    settings=None,
    timeout=None,
    version=None,
):
    """
    # pylint: disable=line-too-long
    Create an index template

    name
        The name of the template
    source
        URL to file specifying template definition. Cannot be used in combination with settings or mappings.
    aliases
        Aliases for the index.
    create
        If true, this request cannot replace or update existing index
        templatelastic.
    error_trace
        error_trace
    filter_path
        filter_path
    flat_settings
        Return settings in flat format (default: false)
    index_patterns
        Array of wildcard expressions used to match the names
        of indices during creation.
    mappings
        Mapping for fields in the index.
    master_timeout
        Period to wait for a connection to the master node. If
        no response is received before the timeout expires, the request fails and
        returns an error.
    order
        Order in which Elasticsearch applielastic this template if index matches
        multiple templatelastic. Templatelastic with lower 'order' values are merged first.
        Templatelastic with higher 'order' values are merged later, overriding templates
        with lower valuelastic.
    settings
        Configuration options for the index.
    timeout
        timeout
    version
        ersion number used to manage index templatelastic externally. This
        number is not automatically generated by Elasticsearch.

    CLI Example:

    .. code-block:: bash

     salt myminion elasticsearch.index_template_create testindex_templ
       '{ "template": "logstash-*", "order": 1, "settings": { "number_of_shards": 1 } }'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    if source and (settings or mappings):
        message = "Either settings or source or mappings should be specified but not both."
        raise SaltInvocationError(message)
    src_map = {}
    if source:
        src_map = __salt__["cp.get_file_str"](source, saltenv=__opts__.get("saltenv", "base"))
        settings = src_map.get("settings", settings)
        mappings = src_map.get("mappings", mappings)
    try:
        result = elastic.indices.put_template(
            name=name,
            aliases=aliases,
            create=create,
            error_trace=error_trace,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            index_patterns=index_patterns,
            mappings=mappings,
            master_timeout=master_timeout,
            order=order,
            pretty=pretty,
            settings=settings,
            timeout=timeout,
            version=version,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot create template {name}, server returned errors {err.errors}"
        ) from err


def index_template_delete(
    name,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    Delete an index template (type) along with its data

    name
        The name of the template
    master_timeout
        Specify timeout for connection to master
    timeout
        Explicit operation timeout

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_template_delete testindex_templ user
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    try:
        result = elastic.indices.delete_template(
            name=name,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body

        return result.get("acknowledged", False)
    except elasticsearch.exceptions.NotFoundError:
        return True
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot delete template {name}, server returned errors {err.errors}"
        ) from err


def index_template_exists(
    name,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
):
    """
    Return a boolean indicating whether given index template exists

    name
        Comma-separated list of index template namelastic used to limit the request.
        Wildcard (*) expressions are supported.
    master_timeout
        Period to wait for a connection to the master node. If
        no response is received before the timeout expires, the request fails and
        returns an error.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_template_exists testindex_templ
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    try:
        return elastic.indices.exists_index_template(
            name=name,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve template {name}, server returned errors {err.errors}"
        ) from err


def template_exists(
    name,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    flat_settings=False,
    human=None,
    local=False,
    master_timeout=None,
    pretty=None,
):
    """
    Return a boolean indicating whether given index template exists

    name
        Comma-separated list of index template namelastic used to limit the request.
        Wildcard (*) expressions are supported.
    flat_settings
        Return settings in flat format (default: false)
    local
        Return local information, do not retrieve the state from master
        node (default: false)
    master_timeout
        Period to wait for a connection to the master node. If
        no response is received before the timeout expires, the request fails and
        returns an error.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_template_exists testindex_templ
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    try:
        return elastic.indices.exists_template(
            name=name,
            error_trace=error_trace,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            local=local,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve template {name}, server returned errors {err.errors}"
        ) from err


def index_template_get(
    name=None,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    flat_settings=None,
    human=None,
    local=None,
    master_timeout=None,
    pretty=None,
):
    """
    .. versionadded:: 3005.1-4

    Retrieve template definition of index or index/type

    name
        The comma separated namelastic of the index templates
    flat_settings
        Return settings in flat format (default: false)
    local
        Return local information, do not retrieve the state from master
        node (default: false)
    master_timeout
        Explicit operation timeout for connection to master node

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.index_template_get testindex_templ
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.indices.get_template(
            name=name,
            error_trace=error_trace,
            filter_path=filter_path,
            flat_settings=flat_settings,
            human=human,
            local=local,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.exceptions.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot retrieve template {name}, server returned errors {err.errors}"
        ) from err


def geo_ip_stats(
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    pretty=None,
):
    """
    .. versionadded:: 3005.1-4

    Returns statistical information about geoip databases

    https://www.elastic.co/guide/en/elasticsearch/reference/master/geoip-stats-api.html

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.geo_ip_stats
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.ingest.geo_ip_stats(
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            pretty=pretty,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot get geo_ip_stats, server returned errors {err.errors}"
        ) from err


def processor_grok(
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    pretty=None,
):
    """
    .. versionadded:: 3005.1-4

    Returns a list of built-in patterns

    https://www.elastic.co/guide/en/elasticsearch/reference/master/grok-processor.html#grok-processor-rest-get

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.processor_grok
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.ingest.processor_grok(
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            pretty=pretty,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot get built-in patterns, server returned errors {err.errors}"
        ) from err


def pipeline_get(
    id_,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    summary=None,
):
    """
    .. versionadded:: 3005.1-4

    Retrieve Ingest pipeline definition. Available since Elasticsearch 5.0.

    `id_`
        Comma separated list of pipeline ids. Wildcards supported
    master_timeout
        Explicit operation timeout for connection to master node
    summary
        Return pipelinelastic without their definitions (default: false)

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.pipeline_get mypipeline
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.ingest.get_pipeline(
            id=id_,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            summary=summary,
        ).body
    except elasticsearch.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot create pipeline {id}, server returned errors {err.errors}"
        ) from err
    except AttributeError as err:
        raise CommandExecutionError("Method is applicable only for Elasticsearch 5.0+") from err


def pipeline_delete(
    id_,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    .. versionadded:: 3005.1-4

    Delete Ingest pipeline. Available since Elasticsearch 5.0.

    `id_`
        Pipeline ID
    master_timeout
        Explicit operation timeout for connection to master node
    timeout
        Explicit operation timeout

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.pipeline_delete mypipeline
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        ret = elastic.ingest.delete_pipeline(
            id=id_,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
        return ret.get("acknowledged", False)
    except elasticsearch.NotFoundError:
        return True
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot delete pipeline {id}, server returned errors {err.errors}"
        ) from err
    except AttributeError as err:
        raise CommandExecutionError("Method is applicable only for Elasticsearch 5.0+") from err


def pipeline_create(
    id_,
    hosts=None,
    profile=None,
    description=None,
    error_trace=None,
    filter_path=None,
    human=None,
    if_version=None,
    master_timeout=None,
    meta=None,
    on_failure=None,
    pretty=None,
    processors=None,
    timeout=None,
    version=None,
):
    """
    # pylint: disable=line-too-long
    .. versionadded:: 3005.1-4

    Create Ingest pipeline by supplied definition. Available since Elasticsearch 5.0.

    `id_`
        Pipeline id
    description
        Description of the ingest pipeline.
    if_version
        Required version for optimistic concurrency control for pipeline updates
    master_timeout
        Period to wait for a connection to the master node. If
        no response is received before the timeout expires, the request fails and
        returns an error.
    meta
        Optional metadata about the ingest pipeline. May have any contents.
        This map is not automatically generated by Elasticsearch.
    on_failure
        Processors to run immediately after a processor failure. Each
        processor supports a processor-level on_failure value. If a processor without
        an on_failure value fails, Elasticsearch uselastic this pipeline-level parameter
        as a fallback. The processors in this parameter run sequentially in the order
        specified. Elasticsearch will not attempt to run the pipeline's remaining
        processors.
    processors
        Processors used to perform transformations on documents before
        indexing. Processors run sequentially in the order specified.
    timeout
        Period to wait for a response. If no response is received before
        the timeout expires, the request fails and returns an error.
    version
        Version number used by external systems to track ingest pipelinelastic.
        This parameter is intended for external systems only. Elasticsearch does
        not use or validate pipeline version numbers.

    CLI Example:

    .. code-block:: bash

     salt myminion elasticsearch.pipeline_create mypipeline
       '{"description": "my custom pipeline", "processors": [{"set" : {"field": "collector_timestamp_millis",
       "value": "{{_ingest.timestamp}}"}}]}'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    try:
        out = elastic.ingest.put_pipeline(
            id=id_,
            description=description,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            if_version=if_version,
            master_timeout=master_timeout,
            meta=meta,
            on_failure=on_failure,
            pretty=pretty,
            processors=processors,
            timeout=timeout,
            version=version,
        ).body
        return out.get("acknowledged", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot create pipeline {id}, server returned errors {err.errors}"
        ) from err
    except AttributeError as err:
        raise CommandExecutionError("Method is applicable only for Elasticsearch 5.0+") from err


def pipeline_simulate(
    id_=None,
    hosts=None,
    profile=None,
    docs=None,
    error_trace=None,
    filter_path=None,
    human=None,
    pipeline=None,
    pretty=None,
    verbose=False,
):
    """
    # pylint: disable=line-too-long
    .. versionadded:: 3005.1-4

    Simulate existing Ingest pipeline on provided data. Available since Elasticsearch 5.0.

    `id_`
        Pipeline id
    docs:
        Documents
    verbose
        Specify if the output should be more verbose

    CLI Example:

    .. code-block:: bash

     salt myminion elasticsearch.pipeline_simulate mypipeline
       '{"docs":[{"_index":"index","_type":"type","_id":"id","_source":{"foo":"bar"}},
       {"_index":"index","_type":"type","_id":"id","_source":{"foo":"rab"}}]}' verbose=True
    """
    elastic = _get_instance(hosts=hosts, profile=profile)
    try:
        result = elastic.ingest.simulate(
            id=id_,
            docs=docs,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            pipeline=pipeline,
            pretty=pretty,
            verbose=verbose,
        ).body
        return result

    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot simulate pipeline {id}, server returned errors {err.errors}"
        ) from err
    except AttributeError as err:
        raise CommandExecutionError("Method is applicable only for Elasticsearch 5.0+") from err


def script_get(
    id_,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
):
    """
    .. versionadded:: 3005.1-4

    Obtain existing script definition.

    `id_`
        Script ID
    master_timeout
        Specify timeout for connection to master

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.script_template_get mytemplate
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.get_script(
            id=id_,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot obtain search template {id}, server returned errors {err.errors}"
        ) from err


def script_create(
    id_,
    script=None,
    hosts=None,
    profile=None,
    context=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    Create cript by supplied script definition

    .. versionadded:: 3005.1-4

    script
        Script definition

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.script_create mytemplate
        '{"template":{"query":{"match":{"title":"{{query_string}}"}}}}'

    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        result = elastic.put_script(
            id=id_,
            script=script,
            context=context,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot create search template {id}, server returned errors {err.errors}"
        ) from err


def script_delete(
    id_,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    .. versionadded:: 3005.1-4

    Delete existing script.

    `id_`
        Script ID
    master_timeout
        Specify timeout for connection to master
    timeout
        Explicit operation timeout

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.script_delete id=id
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        result = elastic.delete_script(
            id=id_,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.NotFoundError:
        return True
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot delete search template {id}, server returned errors {err.errors}"
        ) from err


def repository_get(
    name,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    local=False,
    master_timeout=None,
    pretty=None,
):
    """
    .. versionadded:: 3005.1-4

    Get existing repository details.

    name
                comma-separated list of repository names
    local
                Return local information, do not retrieve the state from master node (default: false)
    master_timeout
                Explicit operation timeout for connection to master node

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.repository_get testrepo
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.snapshot.get_repository(
            name=name,
            local=local,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot obtain repository {name}, server returned errors {err.errors}"
        ) from err


def repository_cleanup(
    name,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    .. versionadded:: 3005.1-4

    Removelastic stale data from repository

    name
        comma-separated list of repository names
    local
        Return local information, do not retrieve the state from master node (default: false)
    master_timeout
        Explicit operation timeout for connection to master node
    timeout
        Period to wait for a response.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.repository_get testrepo
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.snapshot.cleanup_repository(
            name=name,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
    except elasticsearch.NotFoundError:
        return True
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot obtain repository {name}, server returned errors {err.errors}"
        ) from err


def repository_create(
    name,
    hosts=None,
    profile=None,
    type_=None,
    settings=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    repository=None,
    timeout=None,
    verify=None,
    body=None,
):
    """
    # pylint: disable=line-too-long
    .. versionadded:: 3005.1-4

    Create repository for storing snapshots. Note that shared repository paths have to be specified in path.repo
    Elasticsearch configuration option.

    name
            A repository name
    hosts
        List of hosts to connect
    profile
        Security profile to use
    settings:
            Repository settings definition
    `type_`:
            Repository type
    master_timeout
            Explicit operation timeout for connection to master node
    repository
            Repository
    timeout
            Explicit operation timeout
    verify
            Whether to verify the repository after creation
    body
        Repository definition as in
        https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html
        The use of body is deprecated and it will be disabled in a coming release

    CLI Example:

    .. code-block:: bash

     salt myminion elasticsearch.repository_create testrepo
       '{"type":"fs","settings":{"location":"/tmp/test","compress":true}}'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        if body is not None:
            result = elastic.snapshot.create_repository(name=name, type=type_, settings=body).body
        else:
            result = elastic.snapshot.create_repository(
                name=name,
                type=type_,
                settings=settings,
                error_trace=error_trace,
                filter_path=filter_path,
                human=human,
                master_timeout=master_timeout,
                pretty=pretty,
                repository=repository,
                timeout=timeout,
                verify=verify,
            ).body
        return result.get("acknowledged", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot create repository {name}, server returned errors {err.errors}"
        ) from err


def repository_delete(
    name,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    .. versionadded:: 3005.1-4

    Delete existing repository.

        name
                Name of the snapshot repository to unregister. Wildcard (*) patterns are supported.
        master_timeout
                Explicit operation timeout for connection to master node
        timeout
                Explicit operation timeout

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.repository_delete testrepo
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        result = elastic.snapshot.delete_repository(
            name=name,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.NotFoundError:
        return True
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot delete repository {name}, server returned errors {err.errors}"
        ) from err


def repository_verify(
    name,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    .. versionadded:: 3005.1-4

    Obtain list of cluster nodes which successfully verified this repository.

    name
        Repository name
    master_timeout
        Explicit operation timeout for connection to master node
    timeout
        Explicit operation timeout

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.repository_verify testrepo
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.snapshot.verify_repository(
            name=name,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
    except elasticsearch.NotFoundError:
        return None
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot verify repository {name}, server returned errors {err.errors}"
        ) from err


def snapshot_status(
    hosts=None,
    profile=None,
    repository=None,
    snapshot=None,
    error_trace=None,
    filter_path=None,
    human=None,
    ignore_unavailable=None,
    master_timeout=None,
    pretty=None,
):
    """
    .. versionadded:: 3005.1-4

    Obtain status of all currently running snapshots.

    repository
        Particular repository to look for snapshots
    snapshot
        A comma-separated list of snapshot names
    ignore_unavailable
        Whether to ignore unavailable snapshots, defaults
        to false which means a SnapshotMissingException is thrown
    master_timeout
        Explicit operation timeout for connection to master node

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.snapshot_status ignore_unavailable=True
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.snapshot.status(
            repository=repository,
            snapshot=snapshot,
            ignore_unavailable=ignore_unavailable,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot obtain snapshot status, server returned errors {err.errors}"
        ) from err


def snapshot_clone(
    hosts=None,
    profile=None,
    repository=None,
    indices=None,
    target_snapshot=None,
    snapshot=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
    timeout=None,
):
    """
    .. versionadded:: 3005.1-4

    Clonelastic indices from one snapshot into another snapshot in the same repository.

    repository
        Particular repository to look for snapshots
    indices
        List of indices to snapshot
    snapshot
        The name of the snapshot to clone from
    target_snapshot
        The name of the cloned snapshot to create
    master_timeout
        Explicit operation timeout for connection to master node

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.snapshot_status ignore_unavailable=True
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        result = elastic.snapshot.clone(
            repository=repository,
            indices=indices,
            snapshot=snapshot,
            target_snapshot=target_snapshot,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
            timeout=timeout,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot obtain snapshot status, server returned errors {err.errors}"
        ) from err


def snapshot_get(
    repository,
    snapshot,
    hosts=None,
    profile=None,
    after=None,
    error_trace=None,
    filter_path=None,
    from_sort_value=None,
    human=None,
    ignore_unavailable=False,
    include_repository=None,
    index_details=None,
    index_names=None,
    master_timeout=None,
    offset=None,
    order=None,
    pretty=None,
    size=None,
    slm_policy_filter=None,
    sort=None,
    verbose=None,
):
    """
    .. versionadded:: 3005.1-4

    Obtain snapshot residing in specified repository.

        repository
            Comma-separated list of snapshot repository namelastic used to
            limit the request. Wildcard (*) expressions are supported.
        snapshot
            Comma-separated list of snapshot namelastic to retrieve. Also accepts
            wildcards (*). - To get information about all snapshots in a registered repository,
            use a wildcard (*) or _all. - To get information about any snapshots that
            are currently running, use _current.
        after
            Offset identifier to start pagination from as returned by the next
            field in the response body.
        from_sort_value
            Value of the current sort column at which to start retrieval.
            Can either be a string snapshot- or repository name when sorting by snapshot
            or repository name, a millisecond time value or a number when sorting by
            index- or shard count.
        ignore_unavailable
            If false, the request returns an error for any snapshots
            that are unavailable.
        include_repository
            If true, returns the repository name in each snapshot.
        index_details
            If true, returns additional information about each index
            in the snapshot comprising the number of shards in the index, the total size
            of the index in bytes, and the maximum number of segments per shard in the
            index. Defaults to false, meaning that this information is omitted.
        index_names
            If true, returns the name of each index in each snapshot.
        master_timeout
            Period to wait for a connection to the master node. If
            no response is received before the timeout expires, the request fails and
            returns an error.
        offset
            Numeric offset to start pagination from based on the snapshots
            matching this request. Using a non-zero value for this parameter is mutually
            exclusive with using the after parameter. Defaults to 0.
        order
            Sort order. Valid valuelastic are asc for ascending and desc for descending
            order. Defaults to asc, meaning ascending order.
        size
            Maximum number of snapshots to return. Defaults to 0 which means
            return all that match the request without limit.
        slm_policy_filter
            Filter snapshots by a comma-separated list of SLM policy
            namelastic that snapshots belong to. Also accepts wildcards (*) and combinations
            of wildcards followed by exclude patterns starting with -. To include snapshots
            not created by an SLM policy you can use the special pattern _none that will
            match all snapshots without an SLM policy.
        sort
            Allows setting a sort order for the result. Defaults to start_time,
            i.e. sorting by snapshot start time stamp.
        verbose
            If true, returns additional information about each snapshot such
            as the version of Elasticsearch which took the snapshot, the start and end
            timelastic of the snapshot, and the number of shards snapshotted.

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.snapshot_get testrepo testsnapshot
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.snapshot.get(
            repository=repository,
            snapshot=snapshot,
            ignore_unavailable=ignore_unavailable,
            after=after,
            error_trace=error_trace,
            filter_path=filter_path,
            from_sort_value=from_sort_value,
            human=human,
            include_repository=include_repository,
            index_details=index_details,
            index_names=index_names,
            master_timeout=master_timeout,
            offset=offset,
            order=order,
            pretty=pretty,
            size=size,
            slm_policy_filter=slm_policy_filter,
            sort=sort,
            verbose=verbose,
        ).body
    except elasticsearch.NotFoundError:
        return True
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot obtain details of snapshot {snapshot} in repository {repository}, "
            f"server returned errors {err.errors}"
        ) from err


def snapshot_create(
    repository,
    snapshot,
    hosts=None,
    profile=None,
    error_trace=None,
    feature_states=None,
    filter_path=None,
    human=None,
    ignore_unavailable=None,
    include_global_state=None,
    indices=None,
    master_timeout=None,
    metadata=None,
    partial=None,
    pretty=None,
    wait_for_completion=None,
):
    """
    # pylint: disable=line-too-long
    .. versionadded:: 3005.1-4

    Create snapshot in specified repository by supplied definition.

    repository
        Repository name
    snapshot
        Snapshot name
    feature_states
        Feature statelastic to include in the snapshot. Each feature
        state includelastic one or more system indices containing related data. You can
        view a list of eligible featurelastic using the get features API. If include_global_state
        is true, all current feature statelastic are included by default. If include_global_state
        is false, no feature statelastic are included by default.
    ignore_unavailable
        If true, the request ignorelastic data streams and indices
        in indices that are missing or closed. If false, the request returns
        an error for any data stream or index that is missing or closed.
    include_global_state
        If true, the current cluster state is included
        in the snapshot. The cluster state includelastic persistent cluster settings,
        composable index templates, legacy index templates, ingest pipelines, and
        ILM policielastic. It also includelastic data stored in system indices, such as Watches
        and task records (configurable via feature_states).
    indices
        Data streams and indices to include in the snapshot. Supports
        multi-target syntax. Includelastic all data streams and indices by default.
    master_timeout
        Period to wait for a connection to the master node. If
        no response is received before the timeout expires, the request fails and
        returns an error.
    metadata
        Optional metadata for the snapshot. May have any contents. Must
        be less than 1024 bytelastic. This map is not automatically generated by Elasticsearch.
    partial
        If true, allows restoring a partial snapshot of indices with
        unavailable shards. Only shards that were successfully included in the snapshot
        will be restored. All missing shards will be recreated as empty. If false,
        the entire restore operation will fail if one or more indices included in
        the snapshot do not have all primary shards available.
    wait_for_completion
        If true, the request returns a response when the
        snapshot is complete. If false, the request returns a response when the
        snapshot initializelastic.

    CLI Example:

    .. code-block:: bash

     salt myminion elasticsearch.snapshot_create testrepo testsnapshot
       '{"indices":"index_1,index_2","ignore_unavailable":true,"include_global_state":false}'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        response = elastic.snapshot.create(
            repository=repository,
            snapshot=snapshot,
            error_trace=error_trace,
            feature_states=feature_states,
            filter_path=filter_path,
            human=human,
            ignore_unavailable=ignore_unavailable,
            include_global_state=include_global_state,
            indices=indices,
            master_timeout=master_timeout,
            metadata=metadata,
            partial=partial,
            pretty=pretty,
            wait_for_completion=wait_for_completion,
        ).body
        return response.get("accepted", False)
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot create snapshot {snapshot} in repository {repository}, server returned errors {err.errors}"
        ) from err


def snapshot_restore(
    repository,
    snapshot,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    ignore_index_settings=None,
    ignore_unavailable=None,
    include_aliases=None,
    include_global_state=None,
    index_settings=None,
    indices=None,
    master_timeout=None,
    partial=None,
    pretty=None,
    rename_pattern=None,
    rename_replacement=None,
    wait_for_completion=None,
):
    """
    # pylint: disable=line-too-long
    .. versionadded:: 3005.1-4

    Restore existing snapshot in specified repository by supplied definition.

    repository
        Repository name
    snapshot
        Snapshot name
    ignore_index_settings
        ignore_index_settings
    ignore_unavailable
        ignore_unavailable
    include_aliases
        include_aliases
    include_global_state
        include_global_state
    index_settings
        index_settings
    indices
        A list of indices to restore
    master_timeout
        Explicit operation timeout for connection to master node
    partial
        partial
    rename_pattern
        rename_pattern
    rename_replacement
        rename_replacement
    wait_for_completion
        Should this request wait until the operation has completed before returning

    CLI Example:

    .. code-block:: bash

     salt myminion elasticsearch.snapshot_restore testrepo testsnapshot
       '{"indices":"index_1,index_2","ignore_unavailable":true,"include_global_state":true}'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        response = elastic.snapshot.restore(
            repository=repository,
            snapshot=snapshot,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            ignore_index_settings=ignore_index_settings,
            ignore_unavailable=ignore_unavailable,
            include_aliases=include_aliases,
            include_global_state=include_global_state,
            index_settings=index_settings,
            indices=indices,
            master_timeout=master_timeout,
            partial=partial,
            pretty=pretty,
            rename_pattern=rename_pattern,
            rename_replacement=rename_replacement,
            wait_for_completion=wait_for_completion,
        ).body
        return response.get("accepted", False)
    except elasticsearch.ApiError as err:
        raise CommandExecutionError(
            f"Cannot restore snapshot {snapshot} in repository {repository}, server returned errors {err.errors}"
        ) from err


def snapshot_delete(
    repository,
    snapshot,
    hosts=None,
    profile=None,
    error_trace=None,
    filter_path=None,
    human=None,
    master_timeout=None,
    pretty=None,
):
    """
    .. versionadded:: 3005.1-4

    Delete snapshot from specified repository.

    repository
        Repository name
    snapshot
        Snapshot name
    master_timeout
        Explicit operation timeout for connection to master node

    CLI Example:

    .. code-block:: bash

        salt myminion elasticsearch.snapshot_delete testrepo testsnapshot
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        result = elastic.snapshot.delete(
            repository=repository,
            snapshot=snapshot,
            error_trace=error_trace,
            filter_path=filter_path,
            human=human,
            master_timeout=master_timeout,
            pretty=pretty,
        ).body
        return result.get("acknowledged", False)
    except elasticsearch.NotFoundError:
        return True
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot delete snapshot {snapshot} from repository {repository}, server returned errors {err.errors}"
        ) from err


def flush(
    hosts=None,
    profile=None,
    index=None,
    allow_no_indices=None,
    error_trace=None,
    expand_wildcards=None,
    filter_path=None,
    force=None,
    human=None,
    ignore_unavailable=None,
    pretty=None,
    wait_if_ongoing=None,
):
    """
    # pylint: disable=line-too-long
    .. versionadded:: 3005.1-4

    index: A comma-separated list of index names; use _all or empty string
        for all indices
    allow_no_indices: Whether to ignore if a wildcard indices expression resolves
        into no concrete indices. (This includelastic _all string or when no indices
        have been specified)
    expand_wildcards: Whether to expand wildcard expression to concrete indices
        that are open, closed or both.
        Valid valuelastic are::

            all - Expand to open and closed indices.
            open - Expand only to open indices.
            closed - Expand only to closed indices.
            none - Wildcard expressions are not accepted.

    force: Whether a flush should be forced even if it is not necessarily
        needed ie. if no changelastic will be committed to the index. This is useful if
        transaction log IDs should be incremented even if no uncommitted changes
        are present. (This setting can be considered as internal)
    ignore_unavailable: Whether specified concrete indices should be ignored
        when unavailable (missing or closed)
    wait_if_ongoing: If set to true the flush operation will block until the
        flush can be executed if another flush operation is already executing. The
        default is true. If set to false the flush will be skipped iff if another
        flush operation is already running.


    The defaults settings for the above parameters depend on the API being used.

    CLI Example:

    .. code-block:: bash

     salt myminion elasticsearch.flush index='index1,index2' ignore_unavailable=True
       allow_no_indices=True expand_wildcards='all'
    """
    elastic = _get_instance(hosts=hosts, profile=profile)

    try:
        return elastic.indices.flush(
            index=index,
            allow_no_indices=allow_no_indices,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            filter_path=filter_path,
            force=force,
            human=human,
            ignore_unavailable=ignore_unavailable,
            pretty=pretty,
            wait_if_ongoing=wait_if_ongoing,
        ).body
    except elasticsearch.TransportError as err:
        raise CommandExecutionError(
            f"Cannot flush, server returned errors {err.errors}"
        ) from err

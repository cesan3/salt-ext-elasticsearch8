"""
Salt state module
"""
import logging

import salt.utils.json

log = logging.getLogger(__name__)

try:
    import elasticsearch

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


def index_absent(name, hosts=None, profile=None):
    """
    Ensure that the named index is absent.

    name
        Name of the index to remove
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    try:
        index = __salt__["elasticsearch.index_get"](index=name, hosts=hosts, profile=profile)
        if index and name in index:
            if __opts__.get("test", False):
                ret["comment"] = f"Index {name} will be removed"
                ret["changes"]["old"] = index[name]
                ret["result"] = None
            else:
                ret["result"] = __salt__["elasticsearch.index_delete"](index=name, hosts=hosts, profile=profile)
                if ret["result"]:
                    ret["comment"] = f"Successfully removed index {name}".format(name)
                    ret["changes"]["old"] = index[name]
                else:
                    ret["comment"] = f"Failed to remove index {name} for unknown reasons"
        else:
            ret["comment"] = f"Index {name} is already absent"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret


def index_present(name, hosts=None, profile=None, **kwargs):
    """
    Ensure that the named index is present.

    name
        Name of the index to add
    source
        URL to file specifying index definition. Cannot be used in combination with body.
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

    **Example:**

    .. code-block:: yaml

        # Default settings
        mytestindex:
          elasticsearch_index.present

        # Extra settings
        mytestindex2:
          elasticsearch_index.present:
            - settings:
                index:
                  number_of_shards: 10
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    source = kwargs.pop("source", None)

    try:
        index_exists = __salt__["elasticsearch.index_exists"](index=name, hosts=hosts, profile=profile)
        if not index_exists:
            if __opts__["test"]:
                ret["comment"] = f"Index {name} does not exist and will be created"
                ret["changes"] = {"new": kwargs}
                ret["result"] = None
            else:
                output = __salt__["elasticsearch.index_create"](
                    index=name, hosts=hosts, profile=profile, source=source, **kwargs
                )
                if output:
                    ret["comment"] = f"Successfully created index {name}"
                    ret["changes"] = {
                        "new": __salt__["elasticsearch.index_get"](index=name, hosts=hosts, profile=profile)[name]
                    }
                else:
                    ret["result"] = False
                    ret["comment"] = f"Cannot create index {name}, {output}"
        else:
            ret["comment"] = f"Index {name} is already present"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret


def alias_absent(name, index, hosts=None, profile=None):
    """
    Ensure that the index alias is absent.

    name
        Name of the index alias to remove
    index
        Name of the index for the alias
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    try:
        alias = __salt__["elasticsearch.alias_get"](aliases=name, indices=index, hosts=hosts, profile=profile)
        if alias and alias.get(index, {}).get("aliases", {}).get(name, None) is not None:
            if __opts__["test"]:
                ret["comment"] = f"Alias {name} for index {index} will be removed"
                ret["changes"]["old"] = alias.get(index, {}).get("aliases", {}).get(name, {})
                ret["result"] = None
            else:
                ret["result"] = __salt__["elasticsearch.alias_delete"](
                    aliases=name, indices=index, hosts=hosts, profile=profile
                )
                if ret["result"]:
                    ret["comment"] = f"Successfully removed alias {name} for index {index}"
                    ret["changes"]["old"] = alias.get(index, {}).get("aliases", {}).get(name, {})
                else:
                    ret["comment"] = f"Failed to remove alias {name} for index {index} for unknown reasons"
        else:
            ret["comment"] = f"Alias {name} for index {index} is already absent"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret


def alias_present(name, indices, hosts=None, profile=None, **kwargs):
    """
    Ensure that the named index alias is present.

    name
        Name of the alias
    indices
        Name of the index
    `filter_`
        Optional dict for filters as per
        https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html
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

    **Example:**

    .. code-block:: yaml

        mytestalias:
          elasticsearch.alias_present:
            - index: testindex
            - filter_:
                term:
                  user: kimchy
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    filter_definition = kwargs.get("filter_")

    try:
        alias = __salt__["elasticsearch.alias_get"](aliases=name, indices=indices, hosts=hosts, profile=profile)
        old = {}
        if alias:
            old = alias.get(indices, {}).get("aliases", {}).get(name, {})
        if filter_definition is None:
            filter_definition = {}

        ret["changes"] = __utils__["dictdiffer.deep_diff"](old, filter_definition)

        if ret["changes"] or not filter_definition:
            if __opts__["test"]:
                if not old:
                    ret["comment"] = f"Alias {name} for index {indices} does not exist and will be created"
                else:
                    ret[
                        "comment"
                    ] = f"Alias {name} for index {indices} exists with wrong configuration and will be overridden"

                ret["result"] = None
            else:
                output = __salt__["elasticsearch.alias_create"](
                    alias=name, indices=indices, hosts=hosts, profile=profile, **kwargs
                )
                if output:
                    if not old:
                        ret["comment"] = f"Successfully created alias {name} for index {indices}"
                    else:
                        ret["comment"] = f"Successfully replaced alias {name} for index {indices}"
                else:
                    ret["result"] = False
                    ret["comment"] = f"Cannot create alias {name} for index {indices}, {output}"
        else:
            ret["comment"] = f"Alias {name} for index {indices} is already present"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret


def index_template_absent(name, hosts=None, profile=None):
    """
    Ensure that the named index template is absent.

    name
        Name of the index to remove
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    try:
        index_template = __salt__["elasticsearch.index_template_get"](name=name, hosts=hosts, profile=profile)
        if index_template and name in index_template:
            if __opts__["test"]:
                ret["comment"] = f"Index template {name} will be removed"
                ret["changes"]["old"] = index_template[name]
                ret["result"] = None
            else:
                ret["result"] = __salt__["elasticsearch.index_template_delete"](name=name, hosts=hosts, profile=profile)
                if ret["result"]:
                    ret["comment"] = f"Successfully removed index template {name}"
                    ret["changes"]["old"] = index_template[name]
                else:
                    ret["comment"] = f"Failed to remove index template {name} for unknown reasons"
        else:
            ret["comment"] = f"Index template {name} is already absent"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret


def index_template_present(name, hosts=None, profile=None, check_definition=False, **kwargs):
    """
    Ensure that the named index template is present.

    name
        Name of the index to add
    check_definition
        If the template already exists and the definition is up to date
    source
        URL to file specifying template definition. Cannot be used in combination with body.
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

    **Example:**

    .. code-block:: yaml

        mytestindex2_template:
          elasticsearch.index_template_present:
            - definition:
                template: logstash-*
                order: 1
                settings:
                  number_of_shards: 1
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    try:
        index_template_exists = __salt__["elasticsearch.index_template_exists"](name=name, hosts=hosts, profile=profile)
        settings = kwargs.get("settings")
        mappings = kwargs.get("mappings")
        aliases = kwargs.get("aliases")
        if not index_template_exists:
            if __opts__["test"]:
                ret["comment"] = f"Index template {name} does not exist and will be created"
                ret["changes"] = {"new": {"settings": settings, "mappings": mappings, "aliases": aliases}}
                ret["result"] = None
            else:
                output = __salt__["elasticsearch.index_template_create"](
                    name=name, hosts=hosts, profile=profile, **kwargs
                )
                if output:
                    ret["comment"] = f"Successfully created index template {name}"
                    ret["changes"] = {
                        "new": __salt__["elasticsearch.index_template_get"](name=name, hosts=hosts, profile=profile)[
                            name
                        ]
                    }
                else:
                    ret["result"] = False
                    ret["comment"] = f"Cannot create index template {name}, {output}"
        else:
            if check_definition:
                definition = {"settings": settings, "mappings": mappings, "aliases": aliases}
                if isinstance(definition, str):
                    definition_parsed = salt.utils.json.loads(definition)
                else:
                    definition_parsed = definition
                current_template = __salt__["elasticsearch.index_template_get"](
                    name=name, hosts=hosts, profile=profile
                )[name]
                # Prune empty keys (avoid false positive diff)
                for key in ("mappings", "aliases", "settings"):
                    if current_template[key] == {} and key not in definition_parsed:
                        del current_template[key]
                diff = __utils__["dictdiffer.deep_diff"](current_template, definition_parsed)
                if len(diff) != 0:
                    if __opts__["test"]:
                        ret["comment"] = f"Index template {name} exist but need to be updated"
                        ret["changes"] = diff
                        ret["result"] = None
                    else:
                        output = __salt__["elasticsearch.index_template_create"](name=name, **kwargs)
                        if output:
                            ret["comment"] = f"Successfully updated index template {name}"
                            ret["changes"] = diff
                        else:
                            ret["result"] = False
                            ret["comment"] = f"Cannot update index template {name}, {output}"
                else:
                    ret["comment"] = f"Index template {name} is already present and up to date"
            else:
                ret["comment"] = f"Index template {name} is already present"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret


def pipeline_absent(name, hosts=None, profile=None):
    """
    Ensure that the named pipeline is absent

    name
        Name of the pipeline to remove
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    try:
        pipeline = __salt__["elasticsearch.pipeline_get"](id_=name, hosts=hosts, profile=profile)
        if pipeline and name in pipeline:
            if __opts__["test"]:
                ret["comment"] = f"Pipeline {name} will be removed"
                ret["changes"]["old"] = pipeline[name]
                ret["result"] = None
            else:
                ret["result"] = __salt__["elasticsearch.pipeline_delete"](id_=name, hosts=hosts, profile=profile)
                if ret["result"]:
                    ret["comment"] = f"Successfully removed pipeline {name}"
                    ret["changes"]["old"] = pipeline[name]
                else:
                    ret["comment"] = f"Failed to remove pipeline {name} for unknown reasons"
        else:
            ret["comment"] = f"Pipeline {name} is already absent"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret


def pipeline_present(name, hosts=None, profile=None, **kwargs):
    """
    Ensure that the named pipeline is present.

    name
        Name/ID of the pipeline to add
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
    definition
        Required dict for creation parameters as per
        https://www.elastic.co/guide/en/elasticsearch/reference/master/pipeline.html

    **Example:**

    .. code-block:: yaml

        test_pipeline:
          elasticsearch.pipeline_present:
            - description: example pipeline
            - processors:
              - set:
                  field: collector_timestamp_millis
                  value: '{{ '{{' }}_ingest.timestamp{{ '}}' }}'
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    processors = kwargs.get("processors")
    description = kwargs.get("description")

    definition = {"description": description, "processors": processors}
    try:
        pipeline = __salt__["elasticsearch.pipeline_get"](id_=name, hosts=hosts, profile=profile)
        old = {}
        if pipeline and name in pipeline:
            old = pipeline[name]
        ret["changes"] = __utils__["dictdiffer.deep_diff"](old, definition)

        if ret["changes"] or (not description or not processors):
            if __opts__["test"]:
                if not pipeline:
                    ret["comment"] = f"Pipeline {name} does not exist and will be created"
                else:
                    ret["comment"] = f"Pipeline {name} exists with wrong configuration and will be overridden"

                ret["result"] = None
            else:
                output = __salt__["elasticsearch.pipeline_create"](id_=name, hosts=hosts, profile=profile, **kwargs)
                if output:
                    if not pipeline:
                        ret["comment"] = f"Successfully created pipeline {name}"
                    else:
                        ret["comment"] = f"Successfully replaced pipeline {name}"
                else:
                    ret["result"] = False
                    ret["comment"] = f"Cannot create pipeline {name}, {output}"
        else:
            ret["comment"] = f"Pipeline {name} is already present"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret


def script_absent(name, hosts=None, profile=None):
    """
    Ensure that the script is absent

    name
        Name of the script to remove
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    try:
        template = __salt__["elasticsearch.script_get"](id_=name, hosts=hosts, profile=profile)
        if template:
            if __opts__["test"]:
                ret["comment"] = f"Search template {name} will be removed"
                ret["changes"]["old"] = salt.utils.json.loads(template["template"])
                ret["result"] = None
            else:
                ret["result"] = __salt__["elasticsearch.script_delete"](id_=name, hosts=hosts, profile=profile)
                if ret["result"]:
                    ret["comment"] = f"Successfully removed search template {name}"
                    ret["changes"]["old"] = salt.utils.json.loads(template["template"])
                else:
                    ret["comment"] = f"Failed to remove search template {name} for unknown reasons"
        else:
            ret["comment"] = f"Search template {name} is already absent"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret


def script_present(name, hosts=None, profile=None, **kwargs):
    """
    Ensure that the named script is present.

    name
        Name of the search template to add

    **Example:**

    .. code-block:: yaml

        test_pipeline:
          elasticsearch.script_present:
            - script:
                inline:
                  size: 10
    """

    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    script = kwargs.get("script")

    try:
        template = __salt__["elasticsearch.script_get"](id_=name, hosts=hosts, profile=profile)

        old = {}
        if template:
            old = salt.utils.json.loads(template["template"])

        ret["changes"] = __utils__["dictdiffer.deep_diff"](old, script)

        if ret["changes"] or not script:
            if __opts__["test"]:
                if not template:
                    ret["comment"] = f"Search template {name} does not exist and will be created"
                else:
                    ret[
                        "comment"
                    ] = f"Search template {name} exists with wrong configuration and will be overridden"

                ret["result"] = None
            else:
                output = __salt__["elasticsearch.script_create"](id_=name, hosts=hosts, profile=profile, **kwargs)
                if output:
                    if not template:
                        ret["comment"] = f"Successfully created search template {name}"
                    else:
                        ret["comment"] = f"Successfully replaced search template {name}"
                else:
                    ret["result"] = False
                    ret["comment"] = f"Cannot create search template {name}, {output}"
        else:
            ret["comment"] = f"Search template {name} is already present"
    except Exception as err:  # pylint: disable=broad-except
        ret["result"] = False
        ret["comment"] = str(err)

    return ret

"""
Salt returner module
"""
import logging

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
    # To force a module not to load return something like:
    #   return (False, "The elasticsearch8 returner module is not implemented yet")
    if not HAS_ELASTICSEARCH:
        return (
            False,
            "Cannot load module elasticsearch: elasticsearch librarielastic not found",
        )
    else:
        if ES_MAJOR_VERSION >= 8:
            return __virtualname__
        return (False, "Cannot load the module, elasticserach version is not 8")

def _get_options(ret=None):
    """
    Get the returner options from salt.
    """

    defaults = {
        "debug_returner_payload": False,
        "functions_blacklist": [],
        "index_date": False,
        "master_event_index": "salt-master-event-cache",
        "master_event_doc_type": "default",
        "master_job_cache_index": "salt-master-job-cache",
        "master_job_cache_doc_type": "default",
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "states_order_output": False,
        "states_count": False,
        "states_single_index": False,
    }

    attrs = {
        "debug_returner_payload": "debug_returner_payload",
        "functions_blacklist": "functions_blacklist",
        "index_date": "index_date",
        "master_event_index": "master_event_index",
        "master_event_doc_type": "master_event_doc_type",
        "master_job_cache_index": "master_job_cache_index",
        "master_job_cache_doc_type": "master_job_cache_doc_type",
        "number_of_shards": "number_of_shards",
        "number_of_replicas": "number_of_replicas",
        "states_count": "states_count",
        "states_order_output": "states_order_output",
        "states_single_index": "states_single_index",
    }

    _options = salt.returners.get_returner_options(
        __virtualname__,
        ret,
        attrs,
        __salt__=__salt__,
        __opts__=__opts__,
        defaults=defaults,
    )
    return _options

def _ensure_index(index):
    index_exists = __salt__["elasticsearch.index_exists"](index)
    if not index_exists:
        options = _get_options()

        settings = {
            "number_of_shards": options["number_of_shards"],
            "number_of_replicas": options["number_of_replicas"],
        }
        __salt__["elasticsearch.index_create"]("{}-v1".format(index), settings=settings)
        __salt__["elasticsearch.alias_create"]("{}-v1".format(index), index)

def _convert_keys(data):
    if isinstance(data, dict):
        new_data = {}
        for k, sub_data in data.items():
            if "." in k:
                new_data["_orig_key"] = k
                k = k.replace(".", "_")
            new_data[k] = _convert_keys(sub_data)
    elif isinstance(data, list):
        new_data = []
        for item in data:
            new_data.append(_convert_keys(item))
    else:
        return data

    return new_data

def returner(ret):
    """
    Process the return from Salt
    """

    job_fun = ret["fun"]
    job_fun_escaped = job_fun.replace(".", "_")
    job_id = ret["jid"]
    job_retcode = ret.get("retcode", 1)
    job_success = True if not job_retcode else False

    options = _get_options(ret)

    if job_fun in options["functions_blacklist"]:
        log.info(
            "Won't push new data to Elasticsearch, job with jid=%s and "
            "function=%s which is in the user-defined list of ignored "
            "functions",
            job_id,
            job_fun,
        )
        return
    if ret.get("data", None) is None and ret.get("return") is None:
        log.info(
            "Won't push new data to Elasticsearch, job with jid=%s was not successful",
            job_id,
        )
        return

    # Build the index name
    if options["states_single_index"] and job_fun in STATE_FUNCTIONS:
        index = "salt-{}".format(STATE_FUNCTIONS[job_fun])
    else:
        index = "salt-{}".format(job_fun_escaped)

    if options["index_date"]:
        index = "{}-{}".format(index, datetime.date.today().strftime("%Y.%m.%d"))

    counts = {}

    # Do some special processing for state returns
    if job_fun in STATE_FUNCTIONS:
        # Init the state counts
        if options["states_count"]:
            counts = {
                "succeeded": 0,
                "failed": 0,
            }
        # Prepend each state execution key in ret['return'] with a zero-padded
        # version of the '__run_num__' field allowing the states to be ordered
        # more easily. Change the index to be
        # index to be '<index>-ordered' so as not to clash with the unsorted
        # index data format
        if options["states_order_output"] and isinstance(ret["return"], dict):
            index = "{}-ordered".format(index)
            max_chars = len(str(len(ret["return"])))

            for uid, data in ret["return"].items():
                # Skip keys we've already prefixed
                if uid.startswith(tuple("0123456789")):
                    continue

                # Store the function being called as it's a useful key to search
                decoded_uid = uid.split("_|-")
                ret["return"][uid]["_func"] = "{}.{}".format(
                    decoded_uid[0], decoded_uid[-1]
                )

                # Prefix the key with the run order so it can be sorted
                new_uid = "{}_|-{}".format(
                    str(data["__run_num__"]).zfill(max_chars),
                    uid,
                )

                ret["return"][new_uid] = ret["return"].pop(uid)

        # Catch a state output that has failed and where the error message is
        # not in a dict as expected. This prevents elasticsearch from
        # complaining about a mapping error
        elif not isinstance(ret["return"], dict):
            ret["return"] = {"return": ret["return"]}

        # Need to count state successes and failures
        if options["states_count"]:
            for state_data in ret["return"].values():
                if state_data["result"] is False:
                    counts["failed"] += 1
                else:
                    counts["succeeded"] += 1

    # Ensure the index exists
    _ensure_index(index)

    # Build the payload
    class UTC(tzinfo):
        def utcoffset(self, dt):
            return timedelta(0)

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return timedelta(0)

    utc = UTC()
    data = {
        "@timestamp": datetime.datetime.now(utc).isoformat(),
        "success": job_success,
        "retcode": job_retcode,
        "minion": ret["id"],
        "fun": job_fun,
        "jid": job_id,
        "counts": counts,
        "data": _convert_keys(ret["return"]),
    }

    if options["debug_returner_payload"]:
        log.debug("elasicsearch payload: %s", data)

    # Post the payload
    ret = __salt__["elasticsearch.document_create"](
        index=index, body=salt.utils.json.dumps(data)
    )

def event_return(events):
    """
    Return events to Elasticsearch

    Requires that the `event_return` configuration be set in master config.
    """
    options = _get_options()

    index = options["master_event_index"]

    if options["index_date"]:
        index = "{}-{}".format(index, datetime.date.today().strftime("%Y.%m.%d"))

    _ensure_index(index)

    for event in events:
        data = {"tag": event.get("tag", ""), "data": event.get("data", "")}

    ret = __salt__["elasticsearch.document_create"](
        index=index,
        id=uuid.uuid4(),
        body=salt.utils.json.dumps(data),
    )

def prep_jid(nocache=False, passed_jid=None):  # pylint: disable=unused-argument
    """
    Do any work necessary to prepare a JID, including sending a custom id
    """
    return passed_jid if passed_jid is not None else salt.utils.jid.gen_jid(__opts__)

def save_load(jid, load, minions=None):
    """
    Save the load to the specified jid id

    .. versionadded:: 2015.8.1
    """
    options = _get_options()

    index = options["master_job_cache_index"]

    _ensure_index(index)

    data = {
        "jid": jid,
        "load": load,
    }

    ret = __salt__["elasticsearch.document_create"](
        index=index, id=jid, body=salt.utils.json.dumps(data)
    )

def get_load(jid):
    """
    Return the load data that marks a specified jid

    .. versionadded:: 2015.8.1
    """
    options = _get_options()

    index = options["master_job_cache_index"]

    data = __salt__["elasticsearch.document_get"](
        index=index, id=jid
    )
    if data:
        return salt.utils.json.loads(data)
    return {}

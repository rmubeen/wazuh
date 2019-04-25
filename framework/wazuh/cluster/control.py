# Copyright (C) 2015-2019, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is a free software; you can redistribute it and/or modify it under the terms of GPLv2
import json

from wazuh import common
from wazuh.agent import Agent
from wazuh.cluster import local_client
from wazuh.cluster.common import as_wazuh_object, WazuhJSONEncoder


async def get_nodes(filter_node=None, offset=0, limit=common.database_limit,
                    sort=None, search=None, select=None, filter_type='all'):
    arguments = {'filter_node': filter_node, 'offset': offset, 'limit': limit, 'sort': sort, 'search': search,
                 'select': select, 'filter_type': filter_type}
    result = json.loads(await local_client.execute(command=b'get_nodes',
                                                   data=json.dumps(arguments).encode(),
                                                   wait_for_complete=False),
                        object_hook=as_wazuh_object)
    if isinstance(result, Exception):
        raise result

    return result


async def get_node(filter_node=None, select=None):
    arguments = {'filter_node': filter_node, 'offset': 0, 'limit': common.database_limit, 'sort': None, 'search': None,
                 'select': select, 'filter_type': 'all'}
    node_info_array = json.loads(await local_client.execute(command=b'get_nodes', data=json.dumps(arguments).encode(),
                                                            wait_for_complete=False),
                                 object_hook=as_wazuh_object)
    if isinstance(node_info_array, Exception):
        raise node_info_array

    if len(node_info_array['items']) > 0:
        return node_info_array['items'][0]
    else:
        return {}


async def get_health(filter_node=None):
    result = json.loads(await local_client.execute(command=b'get_health',
                                                   data=json.dumps(filter_node).encode(),
                                                   wait_for_complete=False),
                        object_hook=as_wazuh_object)
    if isinstance(result, Exception):
        raise result
    return result


async def get_agents(filter_node=None, filter_status=None):
    filter_status = ["all"] if not filter_status else filter_status
    filter_node = ["all"] if not filter_node else filter_node
    select_fields = {'id', 'ip', 'name', 'status', 'node_name', 'version'}

    input_json = {'f': Agent.get_agents_overview,
                  'f_kwargs': {
                      'filters': {'status': ','.join(filter_status), 'node_name': ','.join(filter_node)},
                      'limit': None,
                      'select': list(select_fields)
                      },
                  'from_cluster': False,
                  'wait_for_complete': False
                  }

    result = json.loads(await local_client.execute(command=b'dapi',
                                                   data=json.dumps(input_json, cls=WazuhJSONEncoder).encode(),
                                                   wait_for_complete=False),
                        object_hook=as_wazuh_object)

    if isinstance(result, Exception):
        raise result
    # add unknown value to unfilled variables in result. For example, never connected agents will miss the 'version'
    # variable.
    filled_result = [{**r, **{key: 'unknown' for key in select_fields - r.keys()}} for r in result['items']]
    result['items'] = filled_result
    return result

# Copyright (c) 2013 Rackspace, Inc.
# Copyright (c) 2013 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from stevedore import driver

from marconiclient import auth
from marconiclient import errors


def prepare_request(auth_opts=None, data=None, **kwargs):
    """Prepares a request

    This method takes care of authentication
    and all other steps in the preparation chain.

    The request returned by this call is ready to
    be sent to the server.

    :param auth_opts: Auth parameters
    :type auth_opts: `dict`
    :param data: Optional data to send along with the
        request. If data is not None, it'll be serialized.
    :type data: Any primitive type that is json-serializable.
    :param kwargs: Anything accepted by `Request`

    :returns: A `Request` instance ready to be sent.
    :rtype: `Request`
    """

    req = Request(**kwargs)
    auth_backend = auth.get_backend(**(auth_opts or {}))
    # TODO(flaper87): Do something smarter
    # to get the api_version.
    req = auth_backend.authenticate(1, req)

    if data is not None:
        req.content = json.dumps(data)
    return req


class Request(object):
    """General data for a Marconi request

    The idea is to be declarative i.e. specify *what* is desired. It's up to
    the respective transport to turn this into a layer-specific request.

    *NOTE:* This implementation is not definitive and may change.

    :param endpoint: Server's endpoint
    :type endpoint: str
    :param operation: Operation to issue on the endpoint, i.e:
        - get_queues
        - get_messages
    :type operation: str
    :param content: Request's body. Default: None
    :type content: str
    :param params: Query string params. Default: None
    :type params: dict
    :param headers: Request headers. Default: None
    :type headers: dict
    :param api: Api entry point. i.e: 'queues.v1'
    :type api: `six.text_type`.
    """

    def __init__(self, endpoint='', operation='',
                 content=None, params=None,
                 headers=None, api=None):

        self._api = None
        self._api_mod = api

        self.endpoint = endpoint
        self.operation = operation
        self.content = content
        self.params = params or {}
        self.headers = headers or {}

    @property
    def api(self):
        if not self._api and self._api_mod:
            try:
                namespace = 'marconiclient.api'
                mgr = driver.DriverManager(namespace,
                                           self._api_mod,
                                           invoke_on_load=True)
                self._api = mgr.driver
            except RuntimeError as ex:
                raise errors.DriverLoadFailure(self._api_mod, ex)
        return self._api

    def validate(self):
        """Validation shortcut

        Refer to `transport.api.Api.validate` for
        more information about this method.
        """
        return self.api.validate(params=self.params,
                                 content=self.content)

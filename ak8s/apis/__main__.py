#   Copyright 2018 Kai Groner
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
from pathlib import Path

from . import APIRegistry
from .operation import K8sAPIOperation
from .operation import StreamingMixin


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('release', metavar='RELEASE')
    args = parser.parse_args()

    registry = APIRegistry(release=args.release)

    @registry.add_api_base(r'(?:\w+\.)?watch\w+')
    class K8sAPIWatchOperation(StreamingMixin, K8sAPIOperation):
        pass

    @registry.add_api_base(r'(?:\w+\.)?(?:read|list)\w+')
    class K8sAPIReadItemOrCollectionOperation(
            StreamingMixin.bind_stream_condition(lambda self: self.args.get('watch')),
            K8sAPIOperation):
        pass

    @registry.add_api_base(r'readNamespacedPodLogs')
    class K8sAPIPodLogOperation(
            StreamingMixin.bind_stream_condition(lambda self: self.args.get('follow')),
            K8sAPIOperation):
        pass

# ak8s - an asyncio Kubernetes API client

```python3
async def main():
    registry = APIRegistry(release='1.9')

    # TODO: these should be part of a standard config
    @registry.add_api_base(r'(?:\w+\.)?watch\w+')
    class K8sAPIWatchOperation(StreamingMixin, K8sAPIOperation):
        pass

    @registry.add_api_base(r'(?:\w+\.)?(?:read|list)\w+')
    class K8sAPIReadItemOrCollectionOperation(
            StreamingMixin.bind_stream_condition(lambda self: self.args.get('watch')),
            K8sAPIOperation):
        pass

    async with AK8sClient(registry=registry) as ak8s:
        apis = ak8s.bind_api_group(registry.apis)

        # Async API call
        for pod in await apis.core_v1.list_namespaced_pods('default'):
            print(pod)

        # Async streaming API call
        async for ev, pod in apis.core_v1.watch_namespaced_pods('default'):
            print(ev, pod)

        # Async streaming with restarts (understands resource versioning)
        async for ev, pod in apis.core_v1.watch_namespaced_pods.watch('default'):
            print(ev, pod)
```

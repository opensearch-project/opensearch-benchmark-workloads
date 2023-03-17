async def delete_snapshot(opensearch, params):
    await opensearch.snapshot.delete(repository=mandatory(params, "repository", repr(self)), 
        snapshot=mandatory(params, "snapshot", repr(self))

def register(registry):
    registry.register_runner("delete-snapshot", delete_snapshot, async_runner=True)

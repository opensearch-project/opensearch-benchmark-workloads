def put_settings(es, params):
    es.cluster.put_settings(body=params["body"])


def register(registry):
    try:
        from osbenchmark.worker_coordinator.runner import PutSettings
    except ImportError:
        registry.register_runner("put-settings", put_settings)

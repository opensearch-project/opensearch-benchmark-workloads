import random


def random_fare(workload, params, **kwargs):
    print("random_fare called")
    # you must provide all parameters that the runner expects
    return {
        "body": {
            "size": 0,
            "aggs": {
                "fare_ranges": {
                    "range": {
                        "field": "fare_amount",
                        "ranges": [
                            {
                                "from": "%s" % random.randrange(1, 3),
                                "to": "%s" % random.randrange(4, 100)
                            }
                        ]
                    }
                }
            }
        },
        "index": 'nyc_taxis',
        "request-cache": True
    }


def register(registry):
    registry.register_param_source("random-fare-param-source", random_fare)

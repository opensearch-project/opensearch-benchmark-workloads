import random


async def delete_snapshot(opensearch, params):
    await opensearch.snapshot.delete(repository=params["repository"], snapshot=params["snapshot"])


def random_passenger_count(workload, params, **kwargs):
    return {
        "body": {
            "size": 0,
            "query": {
                "range": {
                    "passenger_count": {
                        "gte": random.randrange(1, 2),
                        "lte": random.randrange(2, 4)
                    }
                }
            }
        },
        "index": 'nyc_taxis',
        "request-cache": True
    }


def random_tip_amount(workload, params, **kwargs):
    gte = random.randrange(0, 1) + round(random.random(), 2)
    lte = random.randrange(1, 10) + round(random.random(), 2)
    return {
        "body": {
            "size": 0,
            "query": {
                "range": {
                    "tip_amount": {
                        "gte": gte,
                        "lte": lte
                    }
                }
            }
        },
        "index": 'nyc_taxis',
        "request-cache": True
    }


def random_fare_amount(workload, params, **kwargs):
    gte = random.randrange(0, 10) + round(random.random(), 2)
    lte = random.randrange(10, 100) + round(random.random(), 2)

    return {
        "body": {
            "size": 0,
            "query": {
                "range": {
                    "fare_amount": {
                        "gte": gte,
                        "lte": lte
                    }
                }
            }
        },
        "index": 'nyc_taxis',
        "request-cache": True
    }


def random_total_amount(workload, params, **kwargs):
    gte = random.randrange(1, 4) + round(random.random(), 2)
    lte = random.randrange(4, 50) + round(random.random(), 2)
    return {
        "body": {
            "size": 0,
            "query": {
                "range": {
                    "total_amount": {
                        "gte": gte,
                        "lte": lte
                    }
                }
            }
        },
        "index": 'nyc_taxis',
        "request-cache": True
    }


def random_pickup_datetime(workload, params, **kwargs):
    gte_year = random.randrange(2014, 2017)
    lte_year = random.randrange(2017, 2022)

    gte_month = random.randrange(1, 5)
    lte_month = random.randrange(5, 12)

    gte_day = random.randrange(1, 15)
    lte_day = random.randrange(15, 30)

    # HH:mm:ss
    gte_h = random.randrange(0, 12)
    lte_h = random.randrange(12, 23)

    gte_m = random.randrange(0, 30)
    lte_m = random.randrange(30, 59)

    gte_s = random.randrange(0, 30)
    lte_s = random.randrange(30, 59)

    # Formatting the dates
    final_g_date = f"{gte_year:04d}-{gte_month:02d}-{gte_day:02d} {gte_h:02d}:{gte_m:02d}:{gte_s:02d}"
    final_l_date = f"{lte_year:04d}-{lte_month:02d}-{lte_day:02d} {lte_h:02d}:{lte_m:02d}:{lte_s:02d}"

    return {
        "body": {
            "size": 0,
            "query": {
                "range": {
                    "pickup_datetime": {
                        "gte": final_g_date,
                        "lte": final_l_date
                    }
                }
            }
        },
        "index": 'nyc_taxis',
        "request-cache": True
    }


def random_dropoff_datetime(workload, params, **kwargs):
    gte_year = random.randrange(2014, 2017)
    lte_year = random.randrange(2017, 2022)

    gte_month = random.randrange(1, 5)
    lte_month = random.randrange(5, 12)

    gte_day = random.randrange(1, 15)
    lte_day = random.randrange(15, 30)

    # HH:mm:ss
    gte_h = random.randrange(0, 12)
    lte_h = random.randrange(12, 23)

    gte_m = random.randrange(0, 30)
    lte_m = random.randrange(30, 59)

    gte_s = random.randrange(0, 30)
    lte_s = random.randrange(30, 59)

    # Formatting the dates
    final_g_date = f"{gte_year:04d}-{gte_month:02d}-{gte_day:02d} {gte_h:02d}:{gte_m:02d}:{gte_s:02d}"
    final_l_date = f"{lte_year:04d}-{lte_month:02d}-{lte_day:02d} {lte_h:02d}:{lte_m:02d}:{lte_s:02d}"

    return {
        "body": {
            "size": 0,
            "query": {
                "range": {
                    "dropoff_datetime": {
                        "gte": final_g_date,
                        "lte": final_l_date
                    }
                }
            }
        },
        "index": 'nyc_taxis',
        "request-cache": True
    }


def register(registry):
    registry.register_param_source("random-passenger-count-param-source", random_passenger_count)
    registry.register_param_source("random-tip-amount-param-source", random_tip_amount)
    registry.register_param_source("random-fare-amount-param-source", random_fare_amount)
    registry.register_param_source("random-total-amount-param-source", random_total_amount)
    registry.register_param_source("random-pickup-datetime-param-source", random_pickup_datetime)
    registry.register_param_source("random-dropoff-datetime-param-source", random_dropoff_datetime)
    registry.register_runner("delete-snapshot", delete_snapshot, async_runner=True)

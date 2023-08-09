import random
from datetime import datetime, timedelta


async def delete_snapshot(opensearch, params):
    await opensearch.snapshot.delete(repository=params["repository"], snapshot=params["snapshot"])


def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())),
    )


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
        "request-cache": True,
        "request-timeout": 60
    }


def expensive_1(workload, params, **kwargs):
    return {
        "body": {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "pickup_datetime": {
                                    "gte": '2015-01-01 00:00:00',
                                    "lte": '2015-01-03 00:00:00'
                                }
                            }
                        },
                        {
                            "range": {
                                "dropoff_datetime": {
                                    "gte": '2015-01-01 00:00:00',
                                    "lte": '2015-01-03 00:00:00'
                                }
                            }
                        }
                    ],
                    "must_not": [
                        {
                            "term": {
                                "vendor_id": "Vendor XYZ"
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "avg_surcharge": {
                    "avg": {
                        "field": "surcharge"
                    }
                },
                "sum_total_amount": {
                    "sum": {
                        "field": "total_amount"
                    }
                },
                "vendor_id_terms": {
                    "terms": {
                        "field": "vendor_id",
                        "size": 100
                    },
                    "aggs": {
                        "avg_tip_per_vendor": {
                            "avg": {
                                "field": "tip_amount"
                            }
                        }
                    }
                },
                "pickup_location_grid": {
                    "geohash_grid": {
                        "field": "pickup_location",
                        "precision": 5
                    },
                    "aggs": {
                        "avg_tip_per_location": {
                            "avg": {
                                "field": "tip_amount"
                            }
                        }
                    }
                }
            }
        },
        "index": 'nyc_taxis',
        "request-cache": True,
        "request-timeout": 60
    }


def expensive_2(workload, params, **kwargs):
    start = datetime(2015, 1, 1)
    end = datetime(2016, 12, 31)

    pickup_gte = random_date(start, end)
    pickup_lte = random_date(pickup_gte, end)

    pickup_gte_str = pickup_gte.strftime("%Y-%m-%d %H:%M:%S")
    pickup_lte_str = pickup_lte.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "body": {
                "size": 0,
                "query": {
                    "range": {
                        "pickup_datetime": {
                            "gte": pickup_gte_str,
                            "lte": pickup_lte_str
                        }
                    }
                },
                "aggs": {
                    "vendor_id_terms": {
                        "terms": {
                            "field": "vendor_id",
                            "size": 100
                        },
                        "aggs": {
                            "avg_total_amount": {
                                "avg": {
                                    "field": "total_amount"
                                }
                            },
                            "vendor_name_terms": {
                                "terms": {
                                    "field": "vendor_name.keyword",
                                    "size": 100
                                },
                                "aggs": {
                                    "avg_tip_per_vendor_name": {
                                        "avg": {
                                            "field": "tip_amount"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
        },
        "index": 'nyc_taxis',
        "request-timeout": 60
    }


def expensive_3(workload, params, **kwargs):
    start = datetime(2015, 1, 1)
    end = datetime(2016, 12, 31)

    pickup_gte = random_date(start, end)
    pickup_lte = random_date(pickup_gte, end)

    pickup_gte_str = pickup_gte.strftime("%Y-%m-%d %H:%M:%S")
    pickup_lte_str = pickup_lte.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "body": {
                "size": 0,
                "query": {
                    "range": {
                        "pickup_datetime": {
                            "gte": pickup_gte_str,
                            "lte": pickup_lte_str
                        }
                    }
                },
                "aggs": {
                    "sum_total_amount": {
                        "sum": {
                            "field": "total_amount"
                        }
                    },
                    "sum_tip_amount": {
                        "sum": {
                            "field": "tip_amount"
                        }
                    }
                }
        },
        "index": 'nyc_taxis',
        "request-timeout": 60
    }


def expensive_4(workload, params, **kwargs):
    start = datetime(2015, 1, 1)
    end = datetime(2016, 12, 31)

    pickup_gte = random_date(start, end)
    pickup_lte = random_date(pickup_gte, end)

    pickup_gte_str = pickup_gte.strftime("%Y-%m-%d %H:%M:%S")
    pickup_lte_str = pickup_lte.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "body": {
                "size": 0,
                "query": {
                    "range": {
                        "pickup_datetime": {
                            "gte": pickup_gte_str,
                            "lte": pickup_lte_str
                        }
                    }
                },
                "aggs": {
                    "vendor_id_terms": {
                        "terms": {
                            "field": "vendor_id",
                            "size": 100
                        },
                        "aggs": {
                            "trip_type_terms": {
                                "terms": {
                                    "field": "trip_type",
                                    "size": 100
                                },
                                "aggs": {
                                    "payment_type_terms": {
                                        "terms": {
                                            "field": "payment_type",
                                            "size": 100
                                        },
                                        "aggs": {
                                            "avg_fare_amount": {
                                                "avg": {
                                                    "field": "fare_amount"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        "index": 'nyc_taxis',
        "request-timeout": 60
    }


def register(registry):
    registry.register_param_source("random-passenger-count-param-source", random_passenger_count)
    registry.register_param_source("random-tip-amount-param-source", random_tip_amount)
    registry.register_param_source("random-fare-amount-param-source", random_fare_amount)
    registry.register_param_source("random-total-amount-param-source", random_total_amount)
    registry.register_param_source("random-pickup-datetime-param-source", random_pickup_datetime)
    registry.register_param_source("random-dropoff-datetime-param-source", random_dropoff_datetime)
    registry.register_param_source("expensive-1-aggs-param-source", expensive_1)
    registry.register_param_source("expensive-2-aggs-param-source", expensive_2)
    registry.register_param_source("expensive-3-aggs-param-source", expensive_3)
    registry.register_param_source("expensive-4-aggs-param-source", expensive_4)
    registry.register_runner("delete-snapshot", delete_snapshot, async_runner=True)

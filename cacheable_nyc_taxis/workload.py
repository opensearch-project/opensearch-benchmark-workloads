import random
import json
from .query_value_providers import fn_names, fn_value_generators
from .zipf import precompute_H, zipf_cdf_inverse
from .generate_standard_random_values import NUM_VALUES
import os


async def delete_snapshot(opensearch, params):
    await opensearch.snapshot.delete(repository=params["repository"], snapshot=params["snapshot"])

# Global objects below

standard_fn_values = {} # keeps a list of the standard values for each fn, for use in repeated queries

for fn_name in fn_names: 
    try:
        fp = os.path.dirname(os.path.realpath(__file__)) + "/" + "standard_values/{}_values.json".format(fn_name)
        with open(fp, "r") as f: 
            standard_fn_values[fn_name] = json.load(f)
    except FileNotFoundError: 
        raise Exception("Must generate standard values for {} using generate_standard_random_values.py!".format(fn_name))

# Precompute values needed to draw from the Zipf distribution
alpha = 1 # The skewness of the distribution. Lower alpha -> more spread-out distribubtion. 
# TODO: Allow alpha to be set via workload-params
precomputed_H_values = precompute_H(NUM_VALUES, alpha)

# A helper function used by all param sources to decide whether to create new values or pull from standard values
# fn_name_list should contain all the fn_names you want values for in this query type. 
# For all values, the decision whether to use existing value is the same
def get_values(params, fn_name_list): 
    if random.random() < params["repeat_freq"]: 
        # We should return standard (repeatable) values 
        # First, draw a value from the Zipf distribution. Subtract one to go from [1, N] -> [0, N-1] and make it an index
        i = zipf_cdf_inverse(random.random(), precomputed_H_values) - 1
        # Check this index doesn't exceed the length of the shortest list of standard function values we're using
        shortest_standard_list = min([len(standard_fn_values[fn_name]) for fn_name in fn_name_list]) 
        i = min(i, shortest_standard_list-1)
        # Return the i-th standard value for all the functions in our list
        return [standard_fn_values[fn_name][i] for fn_name in fn_name_list]
    # Otherwise, return a new completely random value
    return [fn_value_generators[fn_name]() for fn_name in fn_name_list]

def get_basic_range_query(field, gte, lte): 
    return {
        "body": {
            "size": 0,
            "query": {
                "range": {
                    field: {
                        "gte": gte,
                        "lte": lte
                    }
                }
            }
        },
        "index": 'nyc_taxis'
    }

# Each specific query has a wrapper, which is actually used a param source, and a function that provides values, 
# which lives in query_value_providers.py. 
# This provider fn is also used to generate standard random values in the first place. 

def cheap_passenger_count(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_passenger_count"])[0]
    # based on random_passenger_count from https://github.com/kiranprakash154/opensearch-benchmark-workloads/blob/kp/custom-workload/nyc_taxis/workload.py
    return get_basic_range_query("passenger_count", val_dict["gte"], val_dict["lte"])

def cheap_tip_amount(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_tip_amount"])[0]
    return get_basic_range_query("tip_amount", val_dict["gte"], val_dict["lte"])


def cheap_fare_amount(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_fare_amount"])[0]
    return get_basic_range_query("fare_amount", val_dict["gte"], val_dict["lte"])

def cheap_total_amount(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_total_amount"])[0]
    return get_basic_range_query("total_amount", val_dict["gte"], val_dict["lte"])

def cheap_pickup(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_pickup"])[0]
    return get_basic_range_query("pickup_datetime", val_dict["gte"], val_dict["lte"])

def cheap_dropoff(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_dropoff"])[0]
    return get_basic_range_query("dropoff_datetime", val_dict["gte"], val_dict["lte"])


# The following are randomized versions of the existing agg operations in nyc_taxis/operations/default.json
def expensive_distance_amount_agg(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_distance"])[0]
    return {
      "body": {
        "size": 0,
        "query": {
          "bool": {
            "filter": {
              "range": {
                "trip_distance": {
                  "lt": val_dict["lte"],
                  "gte": val_dict["gte"]
                }
              }
            }
          }
        },
        "aggs": {
          "distance_histo": {
            "histogram": {
              "field": "trip_distance",
              "interval": 1
            },
            "aggs": {
              "total_amount_stats": {
                "stats": {
                  "field": "total_amount"
                }
              }
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def expensive_autohisto_agg(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_dropoff"])[0]
    return {
      "body": {
        "size": 0,
        "query": {
          "range": {
            "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lte": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "auto_date_histogram": {
              "field": "dropoff_datetime",
              "buckets": 20
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def expensive_date_histogram_agg(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_dropoff"])[0]
    return {
      "body": {
        "size": 0,
        "query": {
          "range": {
              "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lte": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "date_histogram": {
              "field": "dropoff_datetime",
              "calendar_interval": "day"
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def expensive_date_histogram_calendar_interval(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_dropoff"])[0]
    return {
        "body": {
        "size": 0,
        "query": {
          "range": {
            "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lt": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "date_histogram": {
              "field": "dropoff_datetime",
              "calendar_interval": "month"
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def expensive_date_histogram_calendar_interval_with_tz(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_dropoff"])[0]
    return {
      "body": {
        "size": 0,
        "query": {
          "range": {
            "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lt": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "date_histogram": {
              "field": "dropoff_datetime",
              "calendar_interval": "month",
              "time_zone": "America/New_York"
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def expensive_date_histogram_fixed_interval(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_dropoff"])[0]
    return {
      "body": {
        "size": 0,
        "query": {
          "range": {
            "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lt": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "date_histogram": {
              "field": "dropoff_datetime",
              "fixed_interval": "60d"
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def expensive_date_histogram_fixed_interval_with_tz(workload, params, **kwargs):
    val_dict = get_values(params, ["cheap_dropoff"])[0] 
    return {
      "body": {
        "size": 0,
        "query": {
          "range": {
            "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lt": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "date_histogram": {
              "field": "dropoff_datetime",
              "fixed_interval": "60d",
              "time_zone": "America/New_York"
            }
          }
        }
      },
      "index":"nyc_taxis"
    }
def expensive_date_histogram_fixed_interval_with_metrics(workload, params, **kwargs):
    val_dict = get_values(params, ["cheap_dropoff"])[0] 
    return {
      "name": "date_histogram_fixed_interval_with_metrics",
      "operation-type": "search",
      "body": {
        "size": 0,
        "query": {
          "range": {
            "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lt": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "date_histogram": {
              "field": "dropoff_datetime",
              "fixed_interval": "60d"
            },
            "aggs": {
              "total_amount": { "stats": { "field": "total_amount" } },
              "tip_amount": { "stats": { "field": "tip_amount" } },
              "trip_distance": { "stats": { "field": "trip_distance" } }
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def expensive_auto_date_histogram(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_dropoff"])[0] 
    return {
      "body": {
        "size": 0,
        "query": {
          "range": {
            "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lt": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "auto_date_histogram": {
              "field": "dropoff_datetime",
              "buckets": "12"
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def expensive_auto_date_histogram_with_tz(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_dropoff"])[0] 
    return {
      "body": {
        "size": 0,
        "query": {
          "range": {
            "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lt": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "auto_date_histogram": {
              "field": "dropoff_datetime",
              "buckets": "13",
              "time_zone": "America/New_York"
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def expensive_auto_date_histogram_with_metrics(workload, params, **kwargs): 
    val_dict = get_values(params, ["cheap_dropoff"])[0] 
    return {
      "body": {
        "size": 0,
        "query": {
          "range": {
            "dropoff_datetime": {
              "gte": val_dict["gte"],
              "lt": val_dict["lte"]
            }
          }
        },
        "aggs": {
          "dropoffs_over_time": {
            "auto_date_histogram": {
              "field": "dropoff_datetime",
              "buckets": "12"
            },
            "aggs": {
              "total_amount": { "stats": { "field": "total_amount" } },
              "tip_amount": { "stats": { "field": "tip_amount" } },
              "trip_distance": { "stats": { "field": "trip_distance" } }
            }
          }
        }
      },
      "index":"nyc_taxis"
    }

def register(registry):
    registry.register_param_source("cheap-passenger-count-param-source", cheap_passenger_count)
    registry.register_param_source("cheap-tip-amount-param-source", cheap_tip_amount)
    registry.register_param_source("cheap-fare-amount-param-source", cheap_fare_amount)
    registry.register_param_source("cheap-total-amount-param-source", cheap_total_amount)
    registry.register_param_source("cheap-pickup-param-source", cheap_pickup)
    registry.register_param_source("cheap-dropoff-param-source", cheap_dropoff)
    registry.register_param_source("expensive-distance-amount-agg-param-source", expensive_distance_amount_agg)
    registry.register_param_source("expensive-autohisto-agg-param-source", expensive_autohisto_agg)
    registry.register_param_source("expensive-date-histogram-agg-param-source", expensive_date_histogram_agg)
    registry.register_param_source("expensive-date-histogram-calendar-interval-param-source", expensive_date_histogram_calendar_interval)
    registry.register_param_source("expensive-date-histogram-calendar-interval-with-tz-param-source", expensive_date_histogram_calendar_interval_with_tz)
    registry.register_param_source("expensive-date-histogram-fixed-interval-param-source", expensive_date_histogram_fixed_interval)
    registry.register_param_source("expensive-date-histogram-fixed-interval-with-tz-param-source", expensive_date_histogram_fixed_interval_with_tz)
    registry.register_param_source("expensive-date-histogram-fixed-interval-with-metrics-param-source", expensive_date_histogram_fixed_interval_with_metrics)
    registry.register_param_source("expensive-auto-date-histogram-param-source", expensive_auto_date_histogram)
    registry.register_param_source("expensive-auto-date-histogram-with-tz-param-source", expensive_auto_date_histogram_with_tz)
    registry.register_param_source("expensive-auto-date-histogram-with-metrics-param-source", expensive_auto_date_histogram_with_metrics)
    registry.register_runner("delete-snapshot", delete_snapshot, async_runner=True)
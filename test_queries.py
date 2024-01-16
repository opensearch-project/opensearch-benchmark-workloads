from opensearchpy import OpenSearch
import opensearchpy
import requests 
import datetime
import json

client = OpenSearch(
    hosts = [{'host': "localhost", 'port': 9200}],
    http_compress = True, # enables gzip compression for request bodies
    http_auth = ("admin", "admin"),
    use_ssl = False,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False
)

expensive_4_query = query = {
        "size": 100,
        "query": {
        "range": {
            "pickup_datetime": {
            "gte": "2015-01-01 12:45:45",
            "lte": "2015-07-07 12:01:11"
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
        }

medium_query = {
        "size": 100,
        "query": {
        "range": {
            "pickup_datetime": {
            "gte": "2015-01-01 12:45:45",
            "lte": "2015-07-07 12:01:11"
            }
        }
        },
        "aggs": {
        "vendor_id_terms": {
            "terms": {
            "field": "vendor_id",
            "size": 10
            },
        }
        }
        }

small_query = {
        "size": 0,
        "query": {
        "range": {
            "pickup_datetime": {
            "gte": "2015-01-01 12:45:45",
            "lte": "2015-07-07 12:01:11"
            }
        }
        },
        "aggs": {
        "vendor_id_terms": {
            "terms": {
            "field": "vendor_id",
            "size": 10
            },
        }
        }
        }

no_aggs_query = { 
    "size": 0,
        "query": {
        "range": {
            "pickup_datetime": {
            "gte": "2015-01-01 12:45:45",
            "lte": "2015-07-07 12:01:11"
            }
        }
        },
}

complex_no_aggs_query = { 
    "size": 100,
        "query": {
        "range": {
            "dropoff_datetime": {
            "gte": "2015-02-21 12:45:43",
            "lte": "2015-11-24 12:02:13"
            }
        }
        },

}

def send_test_query(): 
    for query, str_name in zip(
        #[expensive_4_query, medium_query, small_query, no_aggs_query, complex_no_aggs_query],
        #["expensive_4_query", "medium_query", "small_query", "no_aggs_query", "complex_no_aggs_query"]):
        [expensive_4_query], ["expensive_4_query"]):
        now = datetime.datetime.now().timestamp()
        response = client.search(
            body = no_aggs_query,
            index = "nyc_taxis",
            request_timeout=120
        )
        elapsed = datetime.datetime.now().timestamp() - now
        print("Results for {}".format(str_name)) 
        print("Time took: {}".format(elapsed))
        print("Response size (len(str(response_dict))): {}".format(len(str(response))))
        print("\n")


send_test_query()

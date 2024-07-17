import random
import datetime

async def delete_snapshot(opensearch, params):
    await opensearch.snapshot.delete(repository=params["repository"], snapshot=params["snapshot"])

# Common helper functions
def random_money_values(max_value):
    gte_cents = random.randrange(0, max_value*100)
    lte_cents = random.randrange(gte_cents, max_value*100)
    return {
        "gte":gte_cents/100,
        "lte":lte_cents/100
    }

def format_date(datetime_obj):
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S") # check this

def random_dates(min_value, max_value):
    # arguments are datetime objects
    min_timestamp = datetime.datetime.timestamp(min_value)
    max_timestamp = datetime.datetime.timestamp(max_value)
    diff = max_timestamp - min_timestamp
    gte_fraction = random.uniform(0, 1)
    lte_fraction = random.uniform(gte_fraction, 1.0)

    gte_date = datetime.datetime.fromtimestamp(min_timestamp + int(gte_fraction * diff))
    lte_date = datetime.datetime.fromtimestamp(min_timestamp + int(lte_fraction * diff))
    return {
        "gte":format_date(gte_date),
        "lte":format_date(lte_date),
        "format":"yyyy-MM-dd HH:mm:ss"
    }

# Standard value sources for our operations

def passenger_count_source():
    gte = random.randrange(1, 5) # assuming passenger count is 1 to 4?
    lte = random.randrange(gte, 5)
    return {
        "gte": gte,
        "lte": lte
    }

def tip_amount_source():
    return random_money_values(10.99)

def fare_amount_source():
    return random_money_values(100.99)

def total_amount_source():
    return random_money_values(111.98)

def date_source():
    return random_dates(datetime.datetime(2015, 1, 1), datetime.datetime(2015, 1, 15))

def trip_distance_source():
    gte = random.randint(0, 10)
    lte = random.randint(gte, 20)
    return {"gte":gte, "lte":lte}

def register(registry):
    registry.register_standard_value_source("cheap-passenger-count", "passenger_count", passenger_count_source)
    registry.register_standard_value_source("cheap-tip-amount", "tip_amount", tip_amount_source)
    registry.register_standard_value_source("cheap-fare-amount", "fare_amount", fare_amount_source)
    registry.register_standard_value_source("cheap-total-amount", "total_amount", total_amount_source)
    registry.register_standard_value_source("cheap-pickup", "pickup_datetime", date_source)
    registry.register_standard_value_source("cheap-dropoff", "dropoff_datetime", date_source)

    registry.register_standard_value_source("distance_amount_agg", "trip_distance", trip_distance_source)
    registry.register_standard_value_source("autohisto_agg", "dropoff_datetime", date_source)
    registry.register_standard_value_source("date_histogram_agg", "dropoff_datetime", date_source)
    registry.register_standard_value_source("date_histogram_calendar_interval", "dropoff_datetime", date_source)
    registry.register_standard_value_source("date_histogram_calendar_interval_with_tz", "dropoff_datetime", date_source)
    registry.register_standard_value_source("date_histogram_fixed_interval", "dropoff_datetime", date_source)
    registry.register_standard_value_source("date_histogram_fixed_interval_with_tz", "dropoff_datetime", date_source)
    registry.register_standard_value_source("date_histogram_fixed_interval_with_metrics", "dropoff_datetime", date_source)
    registry.register_standard_value_source("auto_date_histogram", "dropoff_datetime", date_source)
    registry.register_standard_value_source("auto_date_histogram_with_tz", "dropoff_datetime", date_source)
    registry.register_standard_value_source("auto_date_histogram_with_metrics", "dropoff_datetime", date_source)

    registry.register_runner("delete-snapshot", delete_snapshot, async_runner=True)
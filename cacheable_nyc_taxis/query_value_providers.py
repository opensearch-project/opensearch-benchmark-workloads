# Value providers for queries live in this file

import random
import datetime

# common helper functions 

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
        "lte":format_date(lte_date)
    }


# actual provider functions

def cheap_passenger_count_provider(): 
    gte = random.randrange(1, 5) # assuming passenger count is 1 to 4?
    lte = random.randrange(gte, 5)
    return {
        "gte": gte, 
        "lte": lte
    }

def cheap_tip_amount_provider(): 
    # random dollar + cents values between 0.00 and 10.99
    return random_money_values(10.99)

def cheap_fare_amount_provider(): 
    # random dollar + cents values between 0.00 and 100.99
    return random_money_values(100.99)

def cheap_total_amount_provider(): 
    return random_money_values(111.98)

def cheap_pickup_provider(): 
    # random days between 1/1/2015 and 12/31/2015
    return random_dates(datetime.datetime(2015, 1, 1), datetime.datetime(2015, 1, 15))

def cheap_dropoff_provider(): 
    # random days between 1/1/2015 and 12/31/2015
    # Should be different from pickup, otherwise we will use the same values 
    # for cached queries which have both a pickup and dropoff field, which would give a range of 0 -> 
    # non-representative results 
    return random_dates(datetime.datetime(2015, 1, 1), datetime.datetime(2015, 1, 15))

def cheap_distance_provider(): 
    gte = random.randint(0, 10)
    lte = random.randint(gte, 20)
    return {"gte":gte, "lte":lte}
    


# name for each specific query
fn_names = [
    "cheap_passenger_count",
    "cheap_tip_amount",
    "cheap_fare_amount",
    "cheap_total_amount", 
    "cheap_pickup",
    "cheap_dropoff", 
    "cheap_distance"
]

# the value generator for each specific query
fn_value_generators = {
    "cheap_passenger_count":cheap_passenger_count_provider,
    "cheap_tip_amount":cheap_tip_amount_provider,
    "cheap_fare_amount":cheap_fare_amount_provider,
    "cheap_total_amount":cheap_total_amount_provider, 
    "cheap_pickup":cheap_pickup_provider,
    "cheap_dropoff":cheap_dropoff_provider,
    "cheap_distance":cheap_distance_provider,
    "cheap_distance":cheap_distance_provider
} 


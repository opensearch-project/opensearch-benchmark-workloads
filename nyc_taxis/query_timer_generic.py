import argparse
import random
import time
import requests
from datetime import datetime
from opensearchpy import OpenSearch
import matplotlib.pyplot as plt
import numpy as np


# Define a function to generate random data
def random_date(start, end):
    delta = end - start
    return start + delta * random.random()


# Expensive query to be used
def expensive_1(day, cache, **kwargs):

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
                                "lte": f"2015-01-{day:02d} 11:59:59"
                            }
                        }
                    },
                    {
                        "range": {
                            "dropoff_datetime": {
                                "gte": '2015-01-01 00:00:00',
                                "lte": f"2015-01-{day:02d} 11:59:59"
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
        "request-cache" : cache,
        "request-timeout": 60
    }


# Function to send the query and measure the response time
def send_query_and_measure_time(day, hit_count, endpoint, username, password, cache):

    # start_time = time.time()

    # Assuming you have the 'expensive_1' function declared in the same file
    query = expensive_1(day, cache)

    # Connect to the OpenSearch domain using the provided endpoint and credentials
    os = OpenSearch(
        [endpoint],
        http_auth=(username, password),
        port=443,
        use_ssl=True,
    )

    # Send the query to the OpenSearch domain
    response = os.search(index=query['index'], body=query['body'], request_timeout=60, request_cache=cache)
    took_time = response['took']

    # end_time = time.time()
    # response_time = end_time - start_time
    return took_time


def get_request_cache_stats(endpoint, username, password):
    url = f"{endpoint}/_nodes/stats/indices/request_cache"
    response = requests.get(url, auth=(username, password))

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve request cache stats.")
        return None


def main():
    parser = argparse.ArgumentParser(description='OpenSearch Query Response Time Plotter')
    parser.add_argument('--endpoint', help='OpenSearch domain endpoint (https://example.com)')
    parser.add_argument('--username', help='Username for authentication')
    parser.add_argument('--password', help='Password for authentication')
    parser.add_argument('--days',     help='Number of days the range to keep increasing to')
    parser.add_argument('--cache',    help='true for cache enabled and false otherwise', default='false')
    args = parser.parse_args()

    url = f"{args.endpoint}/nyc_taxis/_cache/clear"
    response = requests.post(url, auth=(args.username, args.password))

    if response.status_code == 200:
        print("Request cache cleared successfully." + str(response))
    else:
        print("Failed to clear request cache." + str(response.status_code))

    data = get_request_cache_stats(args.endpoint, args.username, args.password)
    hit_count = next(iter(data['nodes'].values()))['indices']['request_cache']['hit_count']
    # hit_count = data['nodes']['xxxxx']['indices']['request_cache']['hit_count']

    # Number of times to execute the query and measure the response time
    num_queries = 50
    save_path = '/home/ec2-user/opensearch-benchmark-workloads/nyc_taxis'  # change this to image save path

    miss_took_times = []
    daily_averages = []
    daily_p99_latencies = []

    # Execute the query multiple times and measure the response time
    for day in range(1, int(args.days) + 1):
        print(f"Starting iterations for range : 1 to {day}")
        response_times = []
        for x in range(1, num_queries + 1):
            response_time = send_query_and_measure_time(day, hit_count, args.endpoint, args.username, args.password, args.cache)
            new_hits = next(iter(get_request_cache_stats(args.endpoint, args.username, args.password)['nodes'].values()))[
                'indices']['request_cache']['hit_count']

            if new_hits > hit_count:
                print(f"Hit. Took time: {response_time}")
                hit_count = new_hits
                isHit = True
            else:
                miss_took_times.append(response_time)
                print(f"Miss. Took time: {response_time}")
                isHit = False

            # Append a tuple with response time and hit/miss status
            response_times.append((response_time, isHit))
            print(f"Response {x} received.")

        # Separate response times and hit/miss indicators for plotting
        hit_miss_colors = ['g' if isHit else 'r' for _, isHit in response_times]

        # Calculate the average response time. Add [1:] to response_times_only in line 186 and 188 if calculating for hits,
        # to ignore first miss. 186 is / num_queries for misses, num_queries - 1 for hits.
        response_times_only = [response[0] for response in response_times]
        average_response_time = sum(response_times_only) / (num_queries)
        p99_latency = np.percentile(response_times_only, 99)

        # collating the data
        daily_averages.append(average_response_time)
        daily_p99_latencies.append(p99_latency)

        # Plot the response times on a graph
        plt.scatter(range(1, num_queries + 1), response_times_only, c=hit_miss_colors, label='Response Times')
        plt.axhline(y=average_response_time, color='r', linestyle='--', label='Average Response Time')

        # Find indices of highest hit and miss. Comment out line below if calculating misses. TODO: buggy
        # highest_hit_index = max([i for i, (_, isHit) in enumerate(response_times) if isHit])
        # highest_miss_index = max([i for i, (_, isHit) in enumerate(response_times) if not isHit])

        # Draw lines at the highest hit and miss points
        # plt.axvline(x=highest_hit_index + 1, color='g', linestyle=':', label='Highest Hit')
        # plt.axvline(x=highest_miss_index + 1, color='r', linestyle=':', label='Highest Miss')

        plt.yscale('log')  # Set log scale on y-axis

        # Set x-axis ticks to prevent overlap
        step = max(1, num_queries // 10)  # Display every 10th tick label
        plt.xticks(range(1, num_queries + 1, step), rotation=45)

        # Add a text annotation for the average and p99 response times
        plt.text(num_queries + 0.5, average_response_time, f'Avg: {average_response_time:.2f} ms', color='r', va='center')
        plt.text(num_queries + 0.5, p99_latency, f'p99: {p99_latency:.2f} ms', color='b', va='bottom')

        plt.xlabel('Query Number')
        plt.ylabel('Response Time (milliseconds)')
        plt.title('OpenSearch Query Response Time from Jan 1 to Jan ' + str(day))
        plt.legend()

        plt.tight_layout()  # Ensure labels and annotations fit within the figure
        
        # Save the figure to the specified folder
        save_filename = 'PoC_time_50hits_plot_until_jan' + str(day) + '.png'  # You can change the filename if needed
        save_full_path = f'{save_path}/{save_filename}'
        figure = plt.gcf()
        figure.savefig(save_full_path)
        plt.close(figure)
        plt.close()
        print("Average response time: ", average_response_time)
        print("File saved to ", save_path)

    # print items in tabular
    print("All Average response times: ")
    for avg_time in enumerate(daily_averages, start=1):
        print(f"{avg_time}")

    print("All Miss took times: ")
    for miss_took_time in enumerate(miss_took_times, start=1):
        print(f"{miss_took_time}")

    print("All p99 response times:")
    for daily_p99_latency in enumerate(daily_p99_latencies, start=1):
        print(f"{daily_p99_latency}")

    plt.figure(figsize=(10, 6))
    plt.plot(range(1, int(args.days) + 1), daily_averages, 'r-', label='Average Response Time')
    plt.plot(range(1, int(args.days) + 1), daily_p99_latencies, 'b-', label='p99 Latency')
    plt.xlabel('Day of the Month')
    plt.ylabel('Time (milliseconds)')
    plt.title('OpenSearch Query Response Time and p99 Latency for the Month')
    plt.legend()

    # Save the cumulative figure
    save_full_path_cumulative = f'{save_path}/cumulative_plot.png'
    plt.savefig(save_full_path_cumulative)
    plt.close()

    print("Cumulative file saved to ", save_path)

if __name__ == '__main__':
    main()
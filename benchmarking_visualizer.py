import os
import json
import matplotlib.pyplot as plt
import csv
import pandas as pd
import time
import subprocess
import datetime

results_to_local_path = "./results"
# on ec2, need to run pip3 install pandas, pip3 install matplotlib,
def create_csv(path):
    with open(path + "cache_visualizer.csv", 'w') as file:
        writer_object = csv.writer(file)
        writer_object.writerow(["Timestamp", "Evictions", "Hits", "Misses"])
        print("created file cache_visualizer.")
    with open(path + "cache_visualizer.csv", 'a') as csv_file:
        for json_filename in os.listdir(path):
            if json_filename.endswith('.json'):
                json_file = open(path + json_filename)
                json_data = json.load(json_file)
                node = json_data["nodes"]
                for node_id in node:
                    request_cache = json_data["nodes"][node_id]["indices"]["request_cache"]
                evictions = request_cache["evictions"]
                hits = request_cache["hit_count"]
                misses = request_cache["miss_count"]
                timestamp = format_timestamp(json_filename)
                writer_object = csv.writer(csv_file)
                writer_object.writerow([timestamp, evictions, hits, misses])

def create_sorted_csv(path):
    data = pd.read_csv(path + "cache_visualizer.csv")
    data = data.sort_values(by="Timestamp", ascending=True)
    data.to_csv(path + "sorted_cache_visualizer.csv")

def create_hit_rate_csv(path):
    data = pd.read_csv(path + "sorted_cache_visualizer.csv")
    hit_prev = -1
    miss_prev = -1
    line = 0
    with open(path + "hit_rate.csv", 'w') as hit_rate_csv:
        writer_object = csv.writer(hit_rate_csv)
        writer_object.writerow(["Timestamp", "HitRate"])

    # iterate the sorted_cache_visualizer.csv file to calculate hits rate
    with open(path + "sorted_cache_visualizer.csv", 'r') as sorted_csv_file:
        reader_obj = csv.reader(sorted_csv_file)
        for row in reader_obj:
            if line == 1:
                hit_prev = float(row[3])
                miss_prev = float(row[4])
            elif line > 1:
                hit_curr = float(row[3])
                miss_curr = float(row[4])
                time_stamp = row[1]
                # no increase, meaning the run already ends
                if hit_curr + miss_curr - hit_prev - miss_prev == 0:
                    break
                hit_rate = float((hit_curr - hit_prev) / (hit_curr + miss_curr - hit_prev - miss_prev))
                # write to hit_rate.csv
                with open(path + "hit_rate.csv", 'a') as hit_rate_csv:
                    writer_object = csv.writer(hit_rate_csv)
                    writer_object.writerow([time_stamp, hit_rate])
                hit_prev = hit_curr
                miss_prev = miss_curr
            line += 1

def plot_cache_numbers_vs_time(path):
    data = pd.read_csv(path + "sorted_cache_visualizer.csv")
    plt.figure()
    plt.plot(data.Timestamp, data.Evictions, label="Evictions")
    plt.plot(data.Timestamp, data.Hits, label="Hits")
    plt.plot(data.Timestamp, data.Misses, label="Misses")
    plt.xticks(rotation=90)
    plt.subplots_adjust(bottom=0.4)
    plt.grid(color='lightgray', linestyle='--')
    graph_name = "cache-numbers-vs-time"
    plt.title(graph_name)
    plt.legend()
    plt.xlabel("Timestamp")
    plt.ylabel("Count")
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    graph_path = './graphs/' + graph_name + "_" + timestamp
    plt.savefig(graph_path)
    cmd = "scp {}.png {}.png".format(graph_path, results_to_local_path + "/" + graph_name + "_" + timestamp)
    subprocess.run(cmd, shell=True, capture_output=True)
    plt.show()

def plot_hit_rate_vs_time(path):
    data = pd.read_csv(path + "hit_rate.csv")
    plt.figure()
    plt.ylim(0, 1)
    plt.plot(data.Timestamp, data.HitRate, label="Hit Rate")
    plt.xticks(rotation=90)
    plt.subplots_adjust(bottom=0.4)
    plt.grid(color='lightgray', linestyle='--')
    graph_name = "hit-rate-vs-time"
    plt.title(graph_name)
    plt.legend()
    plt.xlabel("Timestamp")
    plt.ylabel("Hit Rates")
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    graph_path = './graphs/' + graph_name + "_" + timestamp
    plt.savefig(graph_path)
    cmd = "scp {}.png {}.png".format(graph_path, results_to_local_path + "/" + graph_name + "_" + timestamp)
    subprocess.run(cmd, shell=True, capture_output=True)
    plt.show()


def format_timestamp(json_filename):
    raw_date = json_filename[0:-5]
    res = raw_date[:10] + " " + raw_date[11:13] + ":" + raw_date[14:16] + ":" + raw_date[17:]
    return res


def run_cache_graph_generator(path):
    path += "/"
    create_csv(path)
    create_sorted_csv(path)
    create_hit_rate_csv(path)
    plot_hit_rate_vs_time(path)
    plot_cache_numbers_vs_time(path)




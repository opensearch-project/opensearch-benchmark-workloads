import subprocess
import json
import datetime
import time
import os
import shutil

from benchmarking_visualizer import run_cache_graph_generator

node_endpoint = "http://localhost:9200"
freq = 60 # seconds. increase to 60 later
num_same_before_stopping = 3 # if cache stats are unchanged (and > 0) for this many iterations, stop running
tiered_feature_flag_enabled = True
stop_flag = False # don't change this

num_same_counter = 0
last_heap_entry_number = 0
last_heap_entry_number_start_loop = -1

dump_path = "./dump"
out_graph_path = "./graphs"
results_to_local_path = "./results"
out_path_hot_threads = dump_path + "/hot_threads"
out_path_search_queue = dump_path + "/search_queue"
out_path_cache_stats = dump_path + "/cache_stats"
home_path = "/home/ec2-user"
benchmark_output_path = home_path + "/benchmark_output.txt"
formatted_benchmark_output_path = results_to_local_path + "/formatted_benchmark_output.txt"

eviction_start = 0
eviction_finish = 0
miss_start = 0
miss_finish = 0
hit_start = 0
hit_finish = 0
eviction_disk_start = 0
eviction_disk_finish = 0
miss_disk_start = 0
miss_disk_finish = 0
hit_disk_start = 0
hit_disk_finish = 0

run_started = False

def formatted_now(): 
    return datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S")

def run_hot_threads(): 
    cmd = "curl -XGET \"{}/_nodes/hot_threads?pretty\"".format(node_endpoint)
    resp = str(subprocess.run(cmd, shell=True, capture_output=True).stdout)
    fp = out_path_hot_threads + "/" + formatted_now() + ".txt"
    with open(fp, "w") as f: 
        f.write(resp)

def run_search_queue(): 
    cmd = "curl -XGET \"{}/_nodes/thread_pool?pretty\"".format(node_endpoint)
    resp = json.loads(subprocess.run(cmd, shell=True, capture_output=True).stdout)
    fp = out_path_search_queue + "/" + formatted_now() + ".json"
    with open(fp, "w") as f: 
        json.dump(resp, f)

def do_start_loop(resp):
    global last_heap_entry_number_start_loop, eviction_start, hit_start, miss_start, eviction_disk_start, hit_disk_start, miss_disk_start
    node_name = next(iter(resp["nodes"]))
    rc_info = resp["nodes"][node_name]["indices"]["request_cache"]
    if tiered_feature_flag_enabled:
        heap_entries = int(rc_info["entries"])
    else:
        heap_entries = rc_info["memory_size_in_bytes"]  # dont have entries on main
    if heap_entries != last_heap_entry_number_start_loop and last_heap_entry_number_start_loop != -1:
        # run started, seeing changes in heap entries, record the starting cache numbers
        eviction_start = int(rc_info["evictions"])
        hit_start = int(rc_info["hit_count"])
        miss_start = int(rc_info["miss_count"])
        if "tiers" in rc_info:
            disk_layer = rc_info["tiers"]["disk"]
            eviction_disk_start = int(disk_layer["evictions"])
            hit_disk_start = int(disk_layer["hit_count"])
            miss_disk_start = int(disk_layer["miss_count"])
        last_heap_entry_number_start_loop = -1
        return True
    last_heap_entry_number_start_loop = heap_entries


def do_stop_loop(resp): 
    global last_heap_entry_number
    global num_same_counter
    global eviction_finish, hit_finish, miss_finish, eviction_disk_finish, hit_disk_finish, miss_disk_finish
    node_name = next(iter(resp["nodes"]))
    rc_info = resp["nodes"][node_name]["indices"]["request_cache"]
    if tiered_feature_flag_enabled: 
        heap_entries = int(rc_info["entries"])
    else: 
        heap_entries = rc_info["memory_size_in_bytes"] # dont have entries on main
    if heap_entries == last_heap_entry_number and heap_entries > 0: 
        num_same_counter += 1
    last_heap_entry_number = heap_entries
    disk_on = False
    if num_same_counter >= num_same_before_stopping:
        eviction_finish = int(rc_info["evictions"])
        hit_finish = int(rc_info["hit_count"])
        miss_finish = int(rc_info["miss_count"])
        if "tiers" in rc_info:
            disk_layer = rc_info["tiers"]["disk"]
            eviction_disk_finish = int(disk_layer["evictions"])
            hit_disk_finish = int(disk_layer["hit_count"])
            miss_disk_finish = int(disk_layer["miss_count"])
            disk_on = True
        create_cache_number_diff(disk_on)
        return True

def create_cache_number_diff(disk_on):
    out_path_cache_number_diff = results_to_local_path + "/cache_number_diff.txt"
    with open(out_path_cache_number_diff, "w") as file:
        file.write("Request Cache Section: \n")
        file.write("\tEviction diff is: " + str(eviction_finish - eviction_start) + "\n")
        file.write("\tHit diff is: " + str(hit_finish - hit_start) + "\n")
        file.write("\tMiss diff is: " + str(miss_finish - miss_start) + "\n")
        if disk_on:
            file.write("Disk Section: \n")
            file.write("\tEviction diff is: " + str(eviction_disk_finish - eviction_disk_start) + "\n")
            file.write("\tHit diff is: " + str(hit_disk_finish - hit_disk_start) + "\n")
            file.write("\tMiss diff is: " + str(miss_disk_finish - miss_disk_start) + "\n")

def format_result_table():
    last_table_line_index = -1
    fp = open(benchmark_output_path, "r")
    formatted_fp = open(formatted_benchmark_output_path, "w")
    # get the start line of the most recent run result
    for i, line in enumerate(fp):
        if line.startswith(
                "|                                                 Min Throughput |                              cheap-passenger-count |"):
            last_table_line_index = i

    # write the result table to a new file at benchmark_output_path
    fp = open(benchmark_output_path, "r")
    for i, line in enumerate(fp):
        if i >= last_table_line_index:
            if line.startswith("|"):
                formatted_fp.write(line)
            else:
                break

def run_cache_stats(write_output):
    cmd = "curl -XGET \"{}/_nodes/stats/indices/request_cache?pretty\"".format(node_endpoint)
    resp = json.loads(subprocess.run(cmd, shell=True, capture_output=True).stdout)
    if write_output:
        fp = out_path_cache_stats + "/" + formatted_now() + ".json"
        with open(fp, "w") as f:
            json.dump(resp, f)
    return resp

def clear_cache_stats():
    cmd = "curl -XPOST \"{}/_cache/clear\"".format(node_endpoint)
    resp = subprocess.run(cmd, shell=True, capture_output=True).stdout
    print("cache cleared!")

def zip_results_to_local():
    zip_cmd = "zip -r results.zip results"
    resp = subprocess.run(zip_cmd, shell=True, capture_output=True)

clear_cache_stats()
while True:
    cache_stats = run_cache_stats(False)
    if do_start_loop(cache_stats):
        if not os.path.isdir(out_graph_path):
            os.makedirs(out_graph_path)
        # clear folders of old results
        if os.path.isdir(results_to_local_path):
            shutil.rmtree(results_to_local_path)
        os.makedirs(results_to_local_path)
        if os.path.isdir(dump_path):
            shutil.rmtree(dump_path)
        os.makedirs(dump_path)
        for dir in [out_path_hot_threads, out_path_search_queue, out_path_cache_stats]:
            os.makedirs(dir)
        print("detected benchmarking search stage started")
        while True:
            run_hot_threads()
            run_search_queue()
            cache_stats = run_cache_stats(True)
            if do_stop_loop(cache_stats):
                print("detected benchmarking search stage finished")
                run_cache_graph_generator(out_path_cache_stats)
                format_result_table()
                zip_results_to_local()
                stop_flag = True
                break
            time.sleep(freq)
    if stop_flag:
        break

print("Ending process")

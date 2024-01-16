import subprocess
import json

node_endpoint = "http://localhost:9200"
workload_path = "/home/ec2-user/osb/opensearch-benchmark-workloads/modified_nyc_taxis"
tiered_caching_on = True
test_mode = False
hme_out_fp = "hme_data.txt" #"/home/ec2-user/hme_data.txt"
index_on_first_task = False

def get_command(rf): 
    cmd = "opensearch-benchmark execute-test --pipeline=benchmark-only --workload-path={} --workload-params=\'{{\"requests_cache_enabled\":\"true\", \"repeat_freq\":\"{}\"}}\' --exclude-tasks=delete-index,create-index,check-cluster-health,index,refresh-after-index,force-merge,refresh-after-force-merge,wait-until-merges-finish --target-host={}".format(
        workload_path, 
        rf, 
        node_endpoint
    )
    if test_mode: 
        cmd += " --test-mode"
    return cmd

def get_command_with_index(rf): 
    cmd =  "opensearch-benchmark execute-test --pipeline=benchmark-only --workload-path={} --workload-params=\'{{\"requests_cache_enabled\":\"true\", \"repeat_freq\":\"{}\"}}\' --target-host={}".format(
        workload_path, 
        rf, 
        node_endpoint
    )
    if test_mode: 
        cmd += " --test-mode"
    return cmd

def stats_command(): 
    return "curl -XGET \"{}/_nodes/stats/indices/request_cache\"".format(node_endpoint)

def get_stats_result(): 
    return json.loads(subprocess.run(stats_command(), shell=True, capture_output=True).stdout)

def clear_caches_command(): 
    return "curl -XPOST \"{}/_cache/clear\"".format(node_endpoint)

def check_stats_api_response(stats_result): 
    node_name = next(iter(stats_result["nodes"]))
    if tiered_caching_on:
        assert stats_result["nodes"][node_name]["indices"]["request_cache"]["tiers"]
    else: 
        assert len(stats_result["nodes"][node_name]["indices"]["request_cache"]) == 5

def get_hme(heading): 
    stats_result = get_stats_result() 
    node_name = next(iter(stats_result["nodes"]))
    rc_info = stats_result["nodes"][node_name]["indices"]["request_cache"]
    ret = {"heap":{}}
    keys = ["hit_count", "miss_count", "evictions", "memory_size_in_bytes", "entries"]
    for k in keys: 
        ret["heap"][k] = rc_info[k]
    if tiered_caching_on: 
        ret["disk"] = {}
        disk_info = rc_info["tiers"]["disk"]
        for k in keys: 
            ret["disk"][k] = disk_info[k]
    with open(hme_out_fp, "a+") as f: 
        f.write("HME for {}\n".format(heading))
        f.write("Heap: " + json.dumps(ret["heap"]) + "\n")
        if tiered_caching_on: 
            f.write("Disk: " + json.dumps(ret["disk"]) + "\n")


# Run with repeat_freq = 0, 0.1, 0.3, and 0.65 in sequence. On the first one, also run index commands. 
rf_list = [0, 0.1, 0.3, 0.65]
# wipe existing file values
with open(hme_out_fp, "w") as f: 
    pass


# check tiered caching is on/off as expected 
stats_result = get_stats_result() 
check_stats_api_response(stats_result)
subprocess.run(clear_caches_command(), shell=True)
get_hme("Initial")

if index_on_first_task:
    cmd = get_command_with_index(rf_list[0]) 
else: 
    cmd = get_command(rf_list[0])
subprocess.run(cmd, shell=True)
get_hme("After rf={}".format(rf_list[0]))
subprocess.run(clear_caches_command(), shell=True)

for rf in rf_list[1:]: 
    cmd = get_command(rf) 
    subprocess.run(cmd, shell=True)
    get_hme("After rf={}".format(rf))
    subprocess.run(clear_caches_command(), shell=True)
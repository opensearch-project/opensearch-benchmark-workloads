**Requirements:**
argparse, random, time, requests, datetime, opensearchpy, matplotlib.pyplot, numpy

**Configuring**
The expensive_1 query will be run num_queries times (line 159). It is currently ignoring the randomization and using a hardcoded GTE and LTE, so edit these if you please (lines 39, 40, 47, 48). Set request cache to True or False on line 123 and 112 to enable or disable caching (no need to edit this anywhere else). Note that the node ID in line 167 is hardcoded for this domain, so change it if you are using a different domain. 

For an all-miss run:
- Set request cache to False on line 123 and 112
- Line 186 is divided by num_queries for misses, num_queries - 1 for hits. This is because we want to ignore the first miss in an all-hit run. 
- Make sure there is no [1:] on lines 186 and 188, these would be ignoring the first miss in an all-hit run.

For an all-hit run:
- Set request cache to True on line 123 and 112
- Comment out line 196 if you don't care about the highest miss
- Add [1:] to response_times_only in line 186 and 188 if calculating for hits, to ignore first miss.

**How to run**
cd to the nyc_taxis directory and run python3 python3 query_timer_generic.py {domain_endpoint} {user} {pass}

**Bugs**
- Highest hit and miss are not working, gotta fix that list comprehension. Can look at your console to manually find highest hit and miss for now

**Todo**
- Miss mode and hit mode that will make all the changes above 
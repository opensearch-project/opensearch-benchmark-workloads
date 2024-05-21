import random
import os
import json
from pathlib import Path

from osbenchmark.workload.loader import Downloader
from osbenchmark.workload.loader import Decompressor
from osbenchmark.workload.loader import Decompressor

script_dir = os.path.dirname(os.path.realpath(__file__))

def ingest_pipeline_param_source(workload, params, **kwargs):
    model_id = params['body']['processors'][0]['text_embedding']['model_id']
    if not model_id:
        with open('model_id.json') as f:
            d = json.loads(f.read())
            model_id = d['model_id']
            params['body']['processors'][0]['text_embedding']['model_id'] = model_id
    return params

class QueryParamSource:
    def __init__(self, workload, params, **kwargs):
        if len(workload.indices) == 1:
            index = workload.indices[0].name
            if len(workload.indices[0].types) == 1:
                type = workload.indices[0].types[0].name
            else:
                type = None
        else:
            index = "_all"
            type = None

        self._params = params
        self._params['index'] = index
        self._params['type'] = type
        self._params['variable-queries'] = params.get("variable-queries", 0)
        self.infinite = True

        if self._params['variable-queries'] > 0:
            with open(script_dir + os.sep + 'workload_queries.json', 'r') as f:
                d = json.loads(f.read())
                source_file = d['source-file']
                base_url = d['base-url']
                compressed_bytes = d['compressed-bytes']
                uncompressed_bytes = d['uncompressed-bytes']
                compressed_path = script_dir + os.sep + source_file
                uncompressed_path = script_dir + os.sep + Path(source_file).stem
            if not os.path.exists(compressed_path):
                downloader = Downloader(False, False)
                downloader.download(base_url, None, compressed_path, compressed_bytes)
            if not os.path.exists(uncompressed_path):
                decompressor = Decompressor()
                decompressor.decompress(compressed_path, uncompressed_path, uncompressed_bytes)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        params = self._params
        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
            params['body']['query']['neural']['passage_embedding']['model_id'] = d['model_id']
        count = self._params.get("variable-queries", 0)
        if count > 0:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            with open(script_dir + '/queries.json', 'r') as f:
                lines = f.read().splitlines()
                line =random.choice(lines)
                query_text = json.loads(line)['text']
                params['body']['query']['neural']['passage_embedding']['query_text'] = query_text
        return params

def register(registry):
    registry.register_param_source("semantic-search-source", QueryParamSource)
    registry.register_param_source("create-ingest-pipeline", ingest_pipeline_param_source)

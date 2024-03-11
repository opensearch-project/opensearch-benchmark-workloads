import random
import os
import json
import asyncio
import time
import traceback
from pathlib import Path

from osbenchmark.workload.loader import Downloader
from osbenchmark.workload.loader import Decompressor
from osbenchmark.workload.loader import Decompressor
from osbenchmark.worker_coordinator.runner import Runner
from osbenchmark.worker_coordinator.runner import time_func
from osbenchmark.exceptions import BenchmarkError

script_dir = os.path.dirname(os.path.realpath(__file__))

class DeleteIngestPipeline(Runner):
    @time_func
    async def __call__(self, opensearch, params):
        try:
            resp = await opensearch.ingest.delete_pipeline(id ='nlp-ingest-pipeline')
        except:
            # no current pipeline
            pass

    def __repr__(self, *args, **kwargs):
        return "delete-ingest-pipeline"

class DeleteMlModel(Runner):
    @time_func
    async def __call__(self, opensearch, params):
        body= {
            "query": {
                "match_phrase": {
                    "name": {
                        "query": params.get('model_name')
                    }
                }
            },
            "size": 1000
        }

        model_ids = set()
        try:
            resp = await opensearch.transport.perform_request('POST', '/_plugins/_ml/models/_search', body=body)
            for item in resp['hits']['hits']:
                doc = item.get('_source')
                if doc:
                    id = doc.get('model_id')
                    if id:
                        model_ids.add(id)
        except:
            # no current model
            pass
            
        for model_id in model_ids:
            resp=await opensearch.transport.perform_request('POST', '/_plugins/_ml/models/' + model_id + '/_undeploy')
            resp=await opensearch.transport.perform_request('DELETE', '/_plugins/_ml/models/' + model_id)
            
    def __repr__(self, *args, **kwargs):
        return "delete-ml-model"

class RegisterMlModel(Runner):
    @time_func
    async def __call__(self, opensearch, params):
        model_name = params.get('model_name')
        model_version = params.get('model_version')
        model_format = params.get('model_format')
        body = {
            "query": {
                "match": {
                    "name": model_name
                }
            },
            "size": 1000
        }
        model_id = None
        try:
            resp = await opensearch.transport.perform_request('POST', '/_plugins/_ml/models/_search', body=body)
            for item in resp['hits']['hits']:
                doc = item.get('_source')
                if doc:
                    model_id = doc.get('model_id')
                    if model_id:
                        break
        except:
            pass

        if not model_id:
            body = {
                "name": model_name,
                "version": model_version,
                "model_format": model_format
            }
            resp = await opensearch.transport.perform_request('POST', '_plugins/_ml/models/_register', body=body)
            task_id = resp.get('task_id')
            timeout = 120
            end = time.time() + timeout
            state = 'CREATED'
            while state == 'CREATED' and time.time() < end:
                await asyncio.sleep(5)
                resp = await opensearch.transport.perform_request('GET', '_plugins/_ml/tasks/' + task_id)
                state = resp.get('state')
            if state == 'FAILED':
                raise BenchmarkError("Failed to register ml-model. Model name: {} version: {} model_format: {}".format(
                    body['name'], body['version'], body['model_format']))
            if state == 'CREATED':
                raise BenchmarkError("Timeout when registering ml-model. Model name: {} version: {} model_format: {}".format(
                    body['name'], body['version'], body['model_format']))
            model_id = resp.get('model_id')

        with open('model_id.json', 'w') as f:
            d = { 'model_id': model_id }
            f.write(json.dumps(d))
                    
    def __repr__(self, *args, **kwargs):
        return "register-ml-model"


class DeployMlModel(Runner):
    @time_func
    async def __call__(self, opensearch, params):
        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
            model_id = d['model_id']

        resp = await opensearch.transport.perform_request('POST', '_plugins/_ml/models/' + model_id + '/_deploy')
        task_id = resp.get('task_id')
        timeout = 120
        end = time.time() + timeout
        state = 'RUNNING'
        while state == 'RUNNING' and time.time() < end:
            await asyncio.sleep(5)
            resp = await opensearch.transport.perform_request('GET', '_plugins/_ml/tasks/' + task_id)
            state = resp.get('state')
        if state == 'FAILED':
            raise BenchmarkError("Failed to deploy ml-model. Model_id: {}".format(model_id))
        if state == 'RUNNING':
            raise BenchmarkError("Timeout when deploying ml-model. Model_id: {}".format(model_id))

    def __repr__(self, *args, **kwargs):
        return "deploy-ml-model"

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
        self._params['variable_queries'] = params.get("variable_queries", 0)
        self.infinite = True

        if self._params['variable_queries'] > 0:
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
        count = self._params.get("variable_queries", 0)
        if count > 0:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            with open(script_dir + '/queries.json', 'r') as f:
                d = json.loads(f.read())
                queries = d['queries']
                count = min(count, len(queries))
                queries = queries[0:count]
                query_text = random.choice(queries)
                params['body']['query']['neural']['passage_embedding']['query_text'] = query_text
        return params

def register(registry):
    registry.register_param_source("semantic-search-source", QueryParamSource)
    registry.register_param_source("create-ingest-pipeline", ingest_pipeline_param_source)
    registry.register_runner("delete-ingest-pipeline", DeleteIngestPipeline(), async_runner=True)
    registry.register_runner("delete-ml-model", DeleteMlModel(), async_runner=True)
    registry.register_runner("register-ml-model", RegisterMlModel(), async_runner=True)
    registry.register_runner("deploy-ml-model", DeployMlModel(), async_runner=True)

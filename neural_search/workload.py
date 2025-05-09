import random
import os
import json
from pathlib import Path

import re
from typing import List
from collections import Counter

from osbenchmark.workload.loader import Downloader
from osbenchmark.workload.loader import Decompressor
from osbenchmark import exceptions

script_dir = os.path.dirname(os.path.realpath(__file__))

def ingest_pipeline_param_source(workload, params, **kwargs):
    processor = params['body']['processors'][0]
    if 'sparse_encoding' in processor:
        model_id = processor['sparse_encoding']['model_id']
        processor_name = 'sparse_encoding'
    elif 'text_embedding' in processor:
        model_id = processor['text_embedding']['model_id']
        processor_name = 'text_embedding'
    elif 'text_image_embedding' in processor:
        model_id = processor['text_image_embedding']['model_id']
        processor_name = 'text_image_embedding'
    else:
        raise Exception('Processor: {} is not supported'.format(processor))

    if not model_id:
        # We don't have to manually provide the model_id.json file, it will be created during register-ml-model operation.
        # See the logic in OSB: https://github.com/opensearch-project/opensearch-benchmark/blob/main/osbenchmark/worker_coordinator/runner.py#L2741
        with open('model_id.json') as f:
            d = json.loads(f.read())
            model_id = d['model_id']
            processor[processor_name]['model_id'] = model_id
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

        self.dataset_name = self.get_dataset_name()
        self.load_queries_file()

    def get_dataset_name(self):
        raise NotImplementedError("Subclasses must implement get_dataset_name()")

    def load_queries_file(self):
        if self._params['variable-queries'] > 0:
            with open(script_dir + os.sep + 'workload_queries.json', 'r') as f:
                data = json.load(f)
                for item in data:
                    if item['name'] == self.dataset_name:
                        source_file = item['source-file']
                        base_url = item['base-url']
                        compressed_bytes = item['compressed-bytes']
                        uncompressed_bytes = item['uncompressed-bytes']
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

class NeuralSparseQueryParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'quora'

    def params(self):
        params = self._params
        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
            params['body']['query']['neural_sparse']['passage_embedding']['model_id'] = d['model_id']

        count = self._params.get("variable-queries", 0)
        if count > 0:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            with open(script_dir + '/queries.json', 'r') as f:
                lines = f.read().splitlines()
                line =random.choice(lines)
                query_text = json.loads(line)['text']
                params['body']['query']['neural_sparse']['passage_embedding']['query_text'] = query_text
        return params

class NeuralHybridQueryParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'quora'

    def params(self):
        params = self._params
        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
            params['body']['query']['hybrid']['queries'][1]['neural']['passage_embedding']['model_id'] = d['model_id']

        count = self._params.get("variable-queries", 0)
        if count > 0:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            with open(script_dir + '/queries.json', 'r') as f:
                lines = f.read().splitlines()
                line = random.choice(lines)
                query_text = json.loads(line)['text']
                params['body']['query']['hybrid']['queries'][0]['match']['text']['query'] = query_text
                params['body']['query']['hybrid']['queries'][1]['neural']['passage_embedding']['query_text'] = query_text
        return params

class NeuralHybridQueryBoolParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'quora'

    def params(self):
        params = self._params
        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
            params['body']['query']['bool']['should'][1]['neural']['passage_embedding']['model_id'] = d['model_id']

        count = self._params.get("variable-queries", 0)
        if count > 0:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            with open(script_dir + '/queries.json', 'r') as f:
                lines = f.read().splitlines()
                line = random.choice(lines)
                query_text = json.loads(line)['text']
                params['body']['query']['bool']['should'][0]['match']['text']['query'] = query_text
                params['body']['query']['bool']['should'][1]['neural']['passage_embedding']['query_text'] = query_text
        return params


class NeuralHybridQueryComplexParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'quora'

    def params(self):
        params = self._params
        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
            params['body']['query']['hybrid']['queries'][2]['neural']['passage_embedding']['model_id'] = d['model_id']

        def tokenize_query(query_text: str) -> List[str]:
            # Convert to lowercase and split into tokens
            # Remove special characters but keep alphanumeric and spaces
            clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', query_text.lower())
            tokens = clean_text.split()
            return tokens

        count = self._params.get("variable-queries", 0)
        if count > 0:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            with open(script_dir + '/queries.json', 'r') as f:
                lines = f.read().splitlines()
                line = random.choice(lines)
                query_text = json.loads(line)['text']

                tokens = tokenize_query(query_text)
                # Get word frequency to identify important terms
                word_freq = Counter(tokens)
                # Create phrases from consecutive words (bigrams)
                phrases = [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]
                # Identify potentially important terms (you might want to customize this)
                important_terms = [word for word, freq in word_freq.items() if len(word) > 2]

                params['body']['query']['hybrid']['queries'][0]['match_phrase']['text']['query'] = query_text
                params['body']['query']['hybrid']['queries'][1]['match']['text']['query'] = " ".join(important_terms)
                params['body']['query']['hybrid']['queries'][2]['neural']['passage_embedding']['query_text'] = query_text

                queries = params['body']['query']['hybrid']['queries']
                current_length = len(queries)
                new_phrase_queries = [
                    {
                        "match_phrase": {
                            "text": {
                                "query": phrase,
                                "boost": 1.5,
                                "slop": 1
                            }
                        }
                    } for phrase in phrases[:2]
                ]

                if current_length == 3:
                    # If we have exactly 3 elements, append new ones (up to the limit of 5)
                    queries.extend(new_phrase_queries)
                else:
                    # If we have more than 3 elements, remove excess elements and add new ones
                    del queries[3:]  # Remove all elements starting from index 3
                    queries.extend(new_phrase_queries)  # Add new phrase queries
        return params

class NeuralSemanticQueryParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'quora'

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
                line = random.choice(lines)
                query_text = json.loads(line)['text']
                params['body']['query']['neural']['passage_embedding']['query_text'] = query_text
        return params

class NeuralMultimodalQueryParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'abo'

    def params(self):
        params = self._params
        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
        params['body']['query']['neural']['vector_embedding']['model_id'] = d['model_id']

        count = self._params.get("variable-queries", 1)

        if count == 0:
            raise exceptions.DataError("variable-queries parameter for multimodal search cannot be 0.")
        if count > 0:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            with open(script_dir + '/abo_queries.json', 'r') as f:
                lines = f.read().splitlines()
                line = random.choice(lines)
                item = json.loads(line)
                query_text = item['image_description']
                query_image = item['image_binary']
                params['body']['query']['neural']['vector_embedding']['query_text'] = query_text
                params['body']['query']['neural']['vector_embedding']['query_image'] = query_image
        return params

def register(registry):
    registry.register_param_source("neural-sparse-search-source", NeuralSparseQueryParamSource)
    registry.register_param_source("neural-hybrid-search-source", NeuralHybridQueryParamSource)
    registry.register_param_source("neural-hybrid-search-bool-source", NeuralHybridQueryBoolParamSource)
    registry.register_param_source("neural-hybrid-search-complex-source", NeuralHybridQueryComplexParamSource)
    registry.register_param_source("neural-semantic-search-source", NeuralSemanticQueryParamSource)
    registry.register_param_source("neural-multimodal-search-source", NeuralMultimodalQueryParamSource)
    registry.register_param_source("create-ingest-pipeline-source", ingest_pipeline_param_source)


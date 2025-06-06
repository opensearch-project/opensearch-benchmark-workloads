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

from nyc_taxis.workload import total_amount_source

script_dir = os.path.dirname(os.path.realpath(__file__))

def get_by_path(data: dict, path: str, default=None):
    """
    Safely retrieve a value from a nested dictionary using dot-separated path.

    :param data: The dictionary to traverse (e.g., params).
    :param path: Dot-separated path string (e.g., "body.query.neural.passage_embedding").
    :param default: Default value to return if any part of the path is missing.
    :return: The value at the specified path, or default if not found.
    """
    keys = path.split(".")
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            if default is not None:
                return default
            else:
                raise KeyError(f"Key '{key}' not found in {data} in path '{path}'")
    return data

def inject_model_id(params: dict, model_id_file: str = "model_id.json"):
    """
    Injects model_id from file into the given nested path + '.model_id'.

    :param params: The dictionary to modify.
    :param model_id_file: File containing a JSON object with 'model_id'.
    """
    with open(model_id_file, "r") as f:
        model_id = json.load(f).get("model_id")
    params["model_id"] = model_id

def inject_query_text(params: dict):
    """
    Injects a random 'query_text' from 'queries.json' in the script directory
    into params at '.query_text'.
    """
    queries_file = os.path.join(script_dir, "queries.json")
    with open(queries_file, "r") as f:
        lines = f.read().splitlines()
        random_line = random.choice(lines)
        query_obj = json.loads(random_line)
        params['query_text'] = query_obj.get("text")


def ingest_pipeline_param_source(workload, params, **kwargs):
    supported_processors = ['sparse_encoding', 'text_embedding', 'text_image_embedding']
    processors = params['body'].get('processors', [])

    found_supported_processor = False

    for processor in processors:
        for name in supported_processors:
            if name in processor:
                found_supported_processor = True
                inject_model_id(processor[name])

    if not found_supported_processor:
        raise ValueError(f"No supported processor types found in: {processors}")

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


class NeuralQueryParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'quora'

    def params(self):
        params = self._params
        is_query_semantic_field = params.get('is_query_semantic_field', False)
        if is_query_semantic_field is True:
            embedding_query = get_by_path(params, "body.query.neural.text")
        else:
            search_operation_name = params.get('name', None)
            if search_operation_name == "semantic-search":
                query_name = "neural"
            elif search_operation_name == "sparse-search":
                query_name = "neural_sparse"
            else:
                raise KeyError(
                    f"Unsupported search operation name: '{search_operation_name}' in NeuralQueryParamSource.")

            nested = params.get('nested', 'False')
            if nested == 'True':
                path_to_neural_query = f"body.query.nested.query.{query_name}"
                if query_name == "neural":
                    embedding_field = 'passage_chunk_embedding.knn'
                else:
                    embedding_field = 'passage_chunk_embedding.sparse_encoding'
            else:
                path_to_neural_query = f"body.query.{query_name}"
                embedding_field = "passage_embedding"
            neural_query = get_by_path(params, path_to_neural_query)
            try:
                embedding_query = neural_query[embedding_field]
            except KeyError:
                raise KeyError(f"Key '{embedding_field}' not found in {neural_query}")

            inject_model_id(embedding_query)

        if params.get("variable-queries", 0) > 0:
            inject_query_text(embedding_query)

        return params

class NeuralHybridQueryParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'quora'

    def params(self):
        params = self._params
        hybrid_queries = params['body']['query']['hybrid']['queries']

        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
            hybrid_queries[1]['neural']['passage_embedding']['model_id'] = d['model_id']

        count = self._params.get("variable-queries", 0)
        if count > 0:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            with open(script_dir + '/queries.json', 'r') as f:
                lines = f.read().splitlines()
                line = random.choice(lines)
                query_text = json.loads(line)['text']
                hybrid_queries[0]['match']['text']['query'] = query_text
                hybrid_queries[1]['neural']['passage_embedding']['query_text'] = query_text
        return params

class NeuralHybridQueryBoolParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'quora'

    def params(self):
        params = self._params
        bool_should_query = params['body']['query']['bool']['should']

        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
            bool_should_query[1]['neural']['passage_embedding']['model_id'] = d['model_id']

        count = self._params.get("variable-queries", 0)
        if count > 0:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            with open(script_dir + '/queries.json', 'r') as f:
                lines = f.read().splitlines()
                line = random.choice(lines)
                query_text = json.loads(line)['text']
                bool_should_query[0]['match']['text']['query'] = query_text
                bool_should_query[1]['neural']['passage_embedding']['query_text'] = query_text
        return params


class NeuralHybridQueryComplexParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'quora'

    def params(self):
        params = self._params
        hybrid_queries = params['body']['query']['hybrid']['queries']

        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
            hybrid_queries[2]['neural']['passage_embedding']['model_id'] = d['model_id']

        def tokenize_query(query_text: str) -> List[str]:
            """
            Tokenizes a query string into a list of individual words by converting to lowercase
            and removing special characters.

            Args:
                query_text (str): The input text string to be tokenized.

            Returns:
                List[str]: A list of lowercase tokens containing only alphanumeric characters.

            Note:
                - Special characters are removed
                - Text is converted to lowercase
                - Only alphanumeric characters and spaces are retained
            """
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

                hybrid_queries[0]['match_phrase']['text']['query'] = query_text
                hybrid_queries[1]['match']['text']['query'] = " ".join(important_terms)
                hybrid_queries[2]['neural']['passage_embedding']['query_text'] = query_text

                current_length = len(hybrid_queries)
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
                    hybrid_queries.extend(new_phrase_queries)
                else:
                    # If we have more than 3 elements, remove excess elements and add new ones
                    del hybrid_queries[3:]  # Remove all elements starting from index 3
                    hybrid_queries.extend(new_phrase_queries)  # Add new phrase queries
        return params

class NeuralMultimodalQueryParamSource(QueryParamSource):
    def get_dataset_name(self):
        return 'abo'

    def params(self):
        params = self._params
        vector_embedding_query = params['body']['query']['neural']['vector_embedding']

        with open('model_id.json', 'r') as f:
            d = json.loads(f.read())
        vector_embedding_query['model_id'] = d['model_id']

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
                vector_embedding_query['query_text'] = query_text
                vector_embedding_query['query_image'] = query_image
        return params

class CreateIndexWithSemanticFieldParamSource:
    def __init__(self, workload, params, **kwargs):
        self.infinite = True
        self.index_name = workload.indices[0].name
        self.index_body  = workload.indices[0].body

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        path_to_semantic_field = "mappings.properties.text"
        semantic_field = get_by_path(self.index_body, path_to_semantic_field)
        inject_model_id(semantic_field)

        return {
            "indices": [
                [self.index_name, self.index_body]
            ]
        }

def register(registry):
    registry.register_param_source("neural-search-source", NeuralQueryParamSource)
    registry.register_param_source("neural-hybrid-search-source", NeuralHybridQueryParamSource)
    registry.register_param_source("neural-hybrid-search-bool-source", NeuralHybridQueryBoolParamSource)
    registry.register_param_source("neural-hybrid-search-complex-source", NeuralHybridQueryComplexParamSource)
    registry.register_param_source("neural-multimodal-search-source", NeuralMultimodalQueryParamSource)
    registry.register_param_source("create-ingest-pipeline-source", ingest_pipeline_param_source)
    registry.register_param_source("create-index-with-semantic-field-source", CreateIndexWithSemanticFieldParamSource)


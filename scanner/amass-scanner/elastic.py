from datetime import datetime
from elasticsearch import Elasticsearch
from os import environ
import logging
import config

class ElasticWrapper:
    def __init__(self):
        self.es = Elasticsearch(hosts=[config.es_host], api_key=(environ.get("ES_USERNAME"), environ.get("ES_PASSWORD")))
        x=1

    def submit_document(self, index, document):
        result = self.es.index(index=index, document=document)
        logging.debug(result)

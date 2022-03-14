from elasticsearch import Elasticsearch
import logging


class ElasticWrapper:
    es_index = None

    def __init__(self, host, port, username, password, **kwargs):
        self.es = Elasticsearch(hosts=[f"{host}:{port}"], api_key=(username, password))
        if "conf" in kwargs:
            for k, v in kwargs['conf'].items():
                self.__setattr__(k, v)

    @staticmethod
    def setup(conf: dict):
        """
        Called in setup to return the instantated object
        """
        return ElasticWrapper(host=conf.get("es_host"), port=conf.get("es_port"), username=conf.get("es_username"),
                              password=conf.get("es_password"), conf=conf)

    def submit_document(self, document):
        result = self.es.index(index=self.es_index, document=document)
        logging.info(f"result of nmap es push: {result}")

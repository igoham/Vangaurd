import os
env = os.environ


RABBIT_MQ_HOST = env.get("RABBITMQ_SERVICE_SERVICE_HOST", "127.0.0.1")
RABBIT_MQ_PORT = env.get("RABBITMQ_SERVICE_SERVICE_PORT", 5672)

scanner_input = env.get("SCANNER_INPUT", "rabbitmq")
scanner_output = env.get("SCANNER_OUTPUT", "elastic")

"""
Elastic Search Configuration options
"""
es_index = "amass_nmap_results"
es_host = env.get("es_host", "192.168.2.207")
es_username = env.get("ES_USERNAME")
es_password = env.get("ES_PASSWORD")

"""
PubSub configuration option
"""
aa = None
rabbitmq_queues = []

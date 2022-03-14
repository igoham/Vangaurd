import os
env = os.environ
es_host = env.get("es_host", "192.168.2.207:9200")
nmap_host = env.get("nmap_host", "127.0.0.1:5000")

RABBIT_MQ_HOST = os.environ.get("RABBITMQ_SERVICE_SERVICE_HOST", "127.0.0.1")
RABBIT_MQ_PORT = os.environ.get("RABBITMQ_SERVICE_SERVICE_PORT", 5672)
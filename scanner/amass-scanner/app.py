import logging

from flask import Flask
from queue import Queue
from threading import Thread
from time import sleep
import pika
import config
import sys
import os
from domainRecon import DomainRecon

logging.basicConfig(filename='amass.log', encoding='utf-8')
root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)
recon = DomainRecon()


def check_for_message():
    queue_name = 'amass_jobs'
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=config.RABBIT_MQ_HOST, port=config.RABBIT_MQ_PORT))
    except pika.exceptions.AMQPConnectionError:
        logging.error(f"Failed to connect to rabbit mq server {config.RABBIT_MQ_HOST}:{config.RABBIT_MQ_PORT}")
        return None
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    logging.info(f"Checking '{queue_name}' queue for domain in rabbitmq")
    method_frame, header_frame, body = channel.basic_get(queue=queue_name)
    if method_frame:
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        return body
    else:
        return None


def start_thread():
    logging.info("Starting queue processing thread")
    worker = Thread(target=process_queue)
    worker.setDaemon(True)
    worker.start()
    logging.info("Thread created")


def process_queue():
    while True:
        # domain = app.queue.get()
        msg = check_for_message()
        if msg is None:
            sleep(15)
        else:
            logging.info(f"Submitting domain '{msg}' to amass enum")
            recon.preform_amass_enum(domain=msg.decode("utf-8"))


app = Flask(__name__)
app.queue = Queue()
start_thread()
logging.info("test msg")

from views import *
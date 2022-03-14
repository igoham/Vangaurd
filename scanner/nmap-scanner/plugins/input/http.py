import json
import pika
import logging
from scanjobs import AmassScanJob


class HttpWrapper:
    type = "http"
    _queue_job_mapping = {"amass_jobs": AmassScanJob}

    def __init__(self, host, port, queue_names):
        self.host = host
        self.port = port
        self.queues = queue_names

    @staticmethod
    def setup(conf):
        return HttpWrapper(host=conf.get("host"), port=conf.get("port"), queue_names=conf.get("queue_names"))

    def check_for_message(self):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
        except pika.exceptions.AMQPConnectionError:
            logging.error(f"Failed to connect to rabbit mq server {self.host}:{self.port}")
            return None
        for queue_name in self.queues:
            channel = connection.channel()
            channel.queue_declare(queue=queue_name)
            logging.info(f"Checking for scan jobs in '{queue_name}' queue in rabbitmq")
            method_frame, header_frame, body = channel.basic_get(queue=queue_name)
            if method_frame:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                if queue_name in self._queue_mapping:
                    job_data = json.loads(body.decode("utf-8"))
                    scan_job = self._queue_job_mapping[queue_name](data=job_data)
                    return scan_job
                else:
                    return body
            else:
                continue
        return None

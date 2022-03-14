

class PubSubWrapper:

    def __init__(self, host, port, queues):
        self.host = host
        self.port = port
        self.queues =queues

    @staticmethod
    def setup(conf: dict):

        return PubSubWrapper(host=conf.get("host"), port=conf.get("port"), queues=conf.get("queues"))

    def check_for_message(self):

        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBIT_MQ_HOST, port=config.RABBIT_MQ_PORT))
        except pika.exceptions.AMQPConnectionError:
            logging.error(f"Failed to connect to rabbit mq server {config.RABBIT_MQ_HOST}:{config.RABBIT_MQ_PORT}")
            return None
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)
        logging.info("Checking for scan jobs in rabbitmq")
        method_frame, header_frame, body = channel.basic_get(queue=queue_name)
        if method_frame:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            return body
        else:
            return None
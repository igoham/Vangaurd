import re

from discord.ext import commands
import os
import logging
import pika
import json


RABBIT_MQ_HOST = os.environ.get("RABBITMQ_SERVICE_SERVICE_HOST", "127.0.0.1")
RABBIT_MQ_PORT = os.environ.get("RABBITMQ_SERVICE_SERVICE_PORT", 5672)
bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    logging.info(f"[LISTENER]Authenticated as {bot.user.name}")


def send_to_queue(msg):
    logging.info(f"CONNECTING to {RABBIT_MQ_HOST} {RABBIT_MQ_PORT}")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_MQ_HOST, port=RABBIT_MQ_PORT))
    channel = connection.channel()
    channel.queue_declare(queue='amass_jobs')
    channel.basic_publish(exchange='', routing_key='amass_jobs', body=str.encode(msg))
    print(f"[+] Sent '{msg}'")
    connection.close()


@bot.command()
async def amass(ctx, domain):
    print(f"Triggering amass recon scan on {domain}")
    if not bool(re.match("[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}", domain)):
        await ctx.send(f"'{domain}' did not pass domain validation")
        return

    await ctx.send(f"[+]Attempting to start amass scan for {domain}")
    try:
        send_to_queue(domain)
    except Exception as e:
        logging.error(f"Failed to send jobs to queue due to {e}")
        await ctx.send(f"[+] Failed to make api request due to {e}")
    else:
        await ctx.send(f"[+]{domain} has been submitted to the amass scanner")
        logging.error(f"[+]{domain} has been submitted to the amass scanner")


@bot.command()
async def queue_length(ctx, queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_MQ_HOST, port=RABBIT_MQ_PORT))
    channel = connection.channel()
    q = channel.queue_declare(queue_name)
    q_len = q.method.message_count
    await ctx.send(f"Queue '{queue_name}' as {q_len} messages")


@bot.command()
async def test(ctx, queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_MQ_HOST, port=RABBIT_MQ_PORT))
    channel = connection.channel()
    method_frame, header_frame, body = channel.basic_get(queue_name)
    if method_frame:
        print(method_frame, header_frame, body)
        channel.basic_ack(method_frame.delivery_tag)
    else:
        print('No message returned')


@bot.command()
async def config(ctx):
    """
    Sends the current config to the discord servicer
    """
    rabbit_mq = {"mq_host": RABBIT_MQ_HOST, "mq_port": RABBIT_MQ_PORT}
    await ctx.send(json.dumps(rabbit_mq))


def main():
    bot.run(os.environ.get("TOKEN"))



if __name__ == '__main__':
    main()



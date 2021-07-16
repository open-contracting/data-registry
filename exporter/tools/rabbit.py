import functools
import logging
import threading

import pika
from django.conf import settings

global connected
connected = False

logger = logging.getLogger('exporter')


def publish(message, routing_key):
    if not connected:
        connect()

    exchange = settings.RABBIT["exchange_name"]

    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),
    )


def connect():
    credentials = pika.PlainCredentials(settings.RABBIT["username"], settings.RABBIT["password"])

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBIT["host"],
            port=settings.RABBIT["port"],
            credentials=credentials,
            blocked_connection_timeout=1800,
            heartbeat=0,
        )
    )

    global channel
    channel = connection.channel()
    channel.exchange_declare(exchange=settings.RABBIT["exchange_name"], durable="true", exchange_type="direct")

    global connected
    connected = True
    return connection, channel


def consume(target_callback, routing_key):
    connection, channel = connect()

    exchange = settings.RABBIT["exchange_name"]
    queue = exchange + routing_key

    channel.queue_declare(queue=queue, durable=True)

    channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)

    channel.basic_qos(prefetch_count=1)

    on_message_callback = functools.partial(on_message, args=(connection, target_callback))
    channel.basic_consume(queue=queue, on_message_callback=on_message_callback)

    channel.start_consuming()

    logger.debug(
        "Consuming messages from exchange {} with routing key {}".format(exchange, routing_key)
    )


def on_message(channel, method_frame, header_frame, body, args):
    (connection, target_callback) = args
    delivery_tag = method_frame.delivery_tag
    t = threading.Thread(target=target_callback, args=(connection, channel, delivery_tag, body))
    t.start()


def ack(connection, channel, delivery_tag):
    logger.debug("ACK message from channel {} with delivery tag {}".format(channel, delivery_tag))
    cb = functools.partial(ack_message, channel, delivery_tag)
    connection.add_callback_threadsafe(cb)


def ack_message(channel, delivery_tag):
    channel.basic_ack(delivery_tag)

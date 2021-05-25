import logging

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


def consume(callback, routing_key):
    if not connected:
        connect()

    exchange = settings.RABBIT["exchange_name"]
    queue = exchange + routing_key

    channel.queue_declare(queue=queue, durable=True)

    channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue, on_message_callback=callback)

    logger.debug(
        f"Consuming messages from exchange {exchange} with routing key {routing_key}"
    )

    channel.start_consuming()

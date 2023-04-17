import pika

def create_rabbitmq_connection(host, port, username, password):
    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(host, port, "/", credentials)
    connection = pika.BlockingConnection(parameters)
    return connection

def publish_message(connection, exchange, routing_key, message_body):
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type="direct")
    channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message_body)

def consume_messages(connection, queue, routing_key, exchange, callback):
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type="direct")
    channel.queue_declare(queue=queue)
    channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)
    channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

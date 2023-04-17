import os
from app.utils.message_queue import create_rabbitmq_connection, consume_messages
from app.services.messaging import notify_customer

def process_message(channel, method, properties, body):
    customer_phone_number, loan_amount = body.decode().split(":")
    loan_amount = float(loan_amount)

    twilio_account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    twilio_auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    twilio_phone_number = os.environ["TWILIO_PHONE_NUMBER"]

    notify_customer(customer_phone_number, loan_amount, twilio_account_sid, twilio_auth_token, twilio_phone_number)

if __name__ == "__main__":
    rabbitmq_host = os.environ["RABBITMQ_HOST"]
    rabbitmq_port = int(os.environ["RABBITMQ_PORT"])
    rabbitmq_username = os.environ["RABBITMQ_USERNAME"]
    rabbitmq_password = os.environ["RABBITMQ_PASSWORD"]

    rabbitmq_connection = create_rabbitmq_connection(rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password)
    consume_messages(rabbitmq_connection, queue="loan_notifications", routing_key="eligible_customers", exchange="loan_notifications", callback=process_message)

import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
from app.utils.message_queue import create_rabbitmq_connection, publish_message

def send_loan_eligibility_message(customer_email, loan_amount):
    msg_body = f'You are eligible for a loan of ${loan_amount:.2f}.'

    msg = MIMEText(msg_body)
    msg['Subject'] = 'Loan Eligibility'
    msg['From'] = 'your_email@example.com'
    msg['To'] = customer_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login('your_email@example.com', 'your_email_password')
        server.send_message(msg)




def send_eligibility_notification(customer_phone_number, loan_amount, rabbitmq_connection):
    message_body = f"{customer_phone_number}:{loan_amount}"
    publish_message(rabbitmq_connection, exchange="loan_notifications", routing_key="eligible_customers", message_body=message_body)


def notify_customer(phone_number, loan_amount, twilio_account_sid, twilio_auth_token, twilio_phone_number):
    """
    Notify a customer via SMS about their loan eligibility.
    
    :param phone_number: str, customer's phone number
    :param loan_amount: float, eligible loan amount
    :param twilio_account_sid: str, Twilio account SID
    :param twilio_auth_token: str, Twilio auth token
    :param twilio_phone_number: str, Twilio phone number to send the SMS from
    """
    client = Client(twilio_account_sid, twilio_auth_token)

    message_body = f"Dear Customer, you are eligible for a loan of ${loan_amount:.2f}. Thank you. If you"

    message = client.messages.create(
        body=message_body,
        from_=twilio_phone_number,
        to=phone_number
    )

    return message.sid

from twilio.rest import Client
from settings import TWILLO_AUTH_TOKEN

account_sid = 'TWILIO_ACCOUNT_SID_REMOVED'
client = Client(account_sid, TWILLO_AUTH_TOKEN)
msg_sid = 'TWILIO_MESSAGING_SERVICE_SID_REMOVED'

def send_sms(phone_number: str, text: str):
  
    message = client.messages.create(
      messaging_service_sid= msg_sid,
      body= text,
      to= phone_number.strip()
    )
    print(message)
    print(message.sid)
    return message.sid
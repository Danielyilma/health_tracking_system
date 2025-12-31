import json
from aio_pika import IncomingMessage

async def on_message(message: IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        routing_key = message.routing_key
        
        print(f" [Notification] Received event: {routing_key}")
        
        if "created" in routing_key:
            print(f"    >> PUSH: New health record for {event.get('username')}! Steps: {event.get('steps')}")
        elif "updated" in routing_key:
             print(f"    >> PUSH: Health record updated for {event.get('username')}. Changes: {event.get('updated_fields')}")
        elif "deleted" in routing_key:
             print(f"    >> PUSH: Health record deleted for {event.get('username')}.")

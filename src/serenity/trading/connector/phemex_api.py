import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time

from math import trunc

import websockets
from phemex import PhemexConnection
from tau.core import Signal, NetworkScheduler, MutableSignal, Event
from tau.signal import Map, Filter

from serenity.trading import OrderPlacer, Order


class WebsocketAuthenticator:
    """
    Authentication mechanism for Phemex private WS API.
    """

    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key

    def get_user_auth_message(self) -> str:
        expiry = trunc(time.time()) + 60
        token = self.api_key + str(expiry)
        token = token.encode('utf-8')
        hmac_key = base64.urlsafe_b64decode(self.secret_key)
        signature = hmac.new(hmac_key, token, hashlib.sha256)
        signature_b64 = signature.hexdigest()

        user_auth = {
            "method": "user.auth",
            "params": [
                "API",
                self.api_key,
                signature_b64,
                expiry
            ],
            "id": 1
        }
        return json.dumps(user_auth)


class OrderEvent:
    pass


class AccountOrderPositionSubscriber:
    logger = logging.getLogger(__name__)

    def __init__(self, auth: WebsocketAuthenticator, scheduler: NetworkScheduler, instance_id: str = 'prod'):
        self.auth = auth
        self.scheduler = scheduler

        self.order_events = MutableSignal()
        self.scheduler.network.attach(self.order_events)

        if instance_id == 'prod':
            self.ws_uri = 'wss://phemex.com/ws'
            self.phemex = PhemexConnection()
        elif instance_id == 'test':
            self.ws_uri = 'wss://testnet.phemex.com/ws'
            self.phemex = PhemexConnection(api_url='https://testnet-api.phemex.com')
        else:
            raise ValueError(f'Unknown instance_id: {instance_id}')

    def start(self):
        network = self.scheduler.get_network()
        messages = MutableSignal()
        json_messages = Map(network, messages, lambda x: json.loads(x))
        json_messages = Filter(network, json_messages,
                               lambda x: x.get('type', None) in ['incremental', 'snapshot'])

        class OrderEventScheduler(Event):
            # noinspection PyShadowingNames
            def __init__(self, sub: AccountOrderPositionSubscriber, json_messages: Signal):
                self.sub = sub
                self.json_messages = json_messages

            def on_activate(self) -> bool:
                if self.json_messages.is_valid():
                    msg = self.json_messages.get_value()
                    accounts = msg['accounts']
                    for account in accounts:
                        orders = account['orders']
                        for order in orders:
                            order_event = OrderEvent()
                            self.sub.scheduler.schedule_update(self.sub.order_events, order_event)
                    return True
                else:
                    return False

        network.connect(json_messages, OrderEventScheduler(self, json_messages))

        # noinspection PyShadowingNames
        async def do_subscribe():
            async with websockets.connect(self.ws_uri) as sock:
                self.logger.info(f'sending Account-Order-Position subscription request')
                auth_msg = self.auth.get_user_auth_message()
                await sock.send(auth_msg)
                error_msg = await sock.recv()
                error_struct = json.loads(error_msg)
                if error_struct['error'] is not None:
                    raise ConnectionError(f'Unable to authenticate: {error_msg}')

                aop_sub_msg = {
                    'id': 2,
                    'method': 'aop.subscribe',
                    'params': []
                }
                await sock.send(json.dumps(aop_sub_msg))
                while True:
                    self.scheduler.schedule_update(messages, await sock.recv())

        asyncio.ensure_future(do_subscribe())


class PhemexOrderPlacer(OrderPlacer):

    def get_order_events(self) -> Signal:
        pass

    def submit(self, order: Order):
        pass

    def cancel(self, order: Order):
        pass

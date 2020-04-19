import abc
import json
import logging
from abc import ABC

from tau.core import MutableSignal, NetworkScheduler
from tornado import httputil, httpclient, websocket
import websockets

from serenity.tickstore.journal import Journal
from tornado.ioloop import IOLoop, PeriodicCallback

APPLICATION_JSON = 'application/json'
DEFAULT_KEEPALIVE_TIMEOUT_MILLIS = 1000
DEFAULT_CONNECT_TIMEOUT_SEC = 60
DEFAULT_REQUEST_TIMEOUT_SEC = 60


class WebsocketSubscriber(ABC):
    logger = logging.getLogger(__name__)

    def __init__(self, symbol: str, journal: Journal, loop: IOLoop, keep_alive_timeout: int,
                 connect_timeout: int, request_timeout: int):
        self.symbol = symbol
        self.appender = journal.create_appender()
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout

        self._ws_connection = None
        self.loop = loop

        # noinspection PyTypeChecker
        PeriodicCallback(self._keep_alive, keep_alive_timeout).start()

    async def connect(self):
        url = self._get_url()
        self.logger.info("connecting to {} and subscribing to {} trades".format(url, self.symbol))
        headers = httputil.HTTPHeaders({'Content-Type': APPLICATION_JSON})
        request = httpclient.HTTPRequest(url=url,
                                         connect_timeout=self.connect_timeout,
                                         request_timeout=self.request_timeout,
                                         headers=headers)

        # noinspection PyAttributeOutsideInit
        self._ws_connection = await websocket.websocket_connect(request)
        self.send(json.dumps(self._create_subscribe_msg()))

        while True:
            msg = await self._ws_connection.read_message()
            if msg is None:
                self._on_connection_close()
                break

            self._on_message(msg)

    def send(self, data: str):
        if not self._ws_connection:
            raise RuntimeError('Websocket connection is closed.')

        self._ws_connection.write_message(data)

    def close(self):
        if not self.appender:
            self.appender.close()
            self.appender = None

        if not self._ws_connection:
            self._ws_connection.close()
            self._ws_connection = None

    def _on_message(self, msg_txt):
        if msg_txt:
            msg = json.loads(msg_txt)
            self._on_message_json(msg)
        else:
            self._on_connection_close()
        pass

    async def _keep_alive(self):
        if self._ws_connection is None:
            self.logger.info('Disconnected; attempting to reconnect in keep alive timer')
            await self.connect()

    def _on_connection_close(self):
        self._ws_connection = None
        pass

    @abc.abstractmethod
    def _get_url(self):
        pass

    @abc.abstractmethod
    def _create_subscribe_msg(self):
        pass

    @abc.abstractmethod
    def _on_message_json(self, msg):
        pass


async def subscribe_trades(uri: str, subscribe_msg: dict, messages: MutableSignal, scheduler: NetworkScheduler):
    async with websockets.connect(uri) as sock:
        await sock.send(json.dumps(subscribe_msg))
        while True:
            scheduler.schedule_update(messages, await sock.recv())

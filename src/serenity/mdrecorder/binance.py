import datetime
import fire
import logging

from serenity.mdrecorder.journal import Journal
from serenity.mdrecorder.subscriber import DEFAULT_KEEPALIVE_TIMEOUT_MILLIS, DEFAULT_CONNECT_TIMEOUT_SEC, \
    DEFAULT_REQUEST_TIMEOUT_SEC, WebsocketSubscriber
from serenity.utils import init_logging
from pathlib import Path
from tornado.ioloop import IOLoop


class BinanceSubscriber(WebsocketSubscriber):

    def __init__(self, symbol: str, journal: Journal, loop: IOLoop = IOLoop.instance(),
                 keep_alive_timeout: int = DEFAULT_KEEPALIVE_TIMEOUT_MILLIS,
                 connect_timeout: int = DEFAULT_CONNECT_TIMEOUT_SEC,
                 request_timeout: int = DEFAULT_REQUEST_TIMEOUT_SEC):
        super().__init__(symbol, journal, loop, keep_alive_timeout, connect_timeout, request_timeout)

    def _get_url(self):
        return 'wss://stream.binance.com:9443/stream'

    def _create_subscribe_msg(self):
        return {
            "method": "SUBSCRIBE",
            "params": ["btcusdt@trade"],
            "id": 1
        }

    def _on_message_json(self, msg):
        if 'stream' in msg:
            self.appender.write_double(datetime.datetime.utcnow().timestamp())
            self.appender.write_long(msg['data']['E'])
            self.appender.write_string(msg['data']['s'])
            self.appender.write_boolean(msg['data']['m'])
            self.appender.write_double(float(msg['data']['q']))
            self.appender.write_double(float(msg['data']['p']))


def subscribe_binance_trades(journal_path: str = '/behemoth/journals/BINANCE_TRADES/BTC-USDT'):
    logger = logging.getLogger(__name__)

    journal = Journal(Path(journal_path))
    subscriber = BinanceSubscriber('BTC-USDT', journal)

    logger.info("journaling ticks to {}".format(journal_path))

    IOLoop.instance().run_sync(subscriber.connect)
    IOLoop.instance().start()


if __name__ == '__main__':
    init_logging()
    fire.Fire(subscribe_binance_trades)

import datetime
import fire
import logging

from cloudwall.serenity.mdrecorder.journal import Journal
from cloudwall.serenity.mdrecorder.subscriber import DEFAULT_KEEPALIVE_TIMEOUT_MILLIS, DEFAULT_CONNECT_TIMEOUT_SEC, \
    DEFAULT_REQUEST_TIMEOUT_SEC, WebsocketSubscriber
from cloudwall.serenity.mdrecorder.utils import init_logging
from pathlib import Path
from tornado.ioloop import IOLoop


class CoinbaseProSubscriber(WebsocketSubscriber):

    def __init__(self, symbol: str, journal: Journal, loop: IOLoop = IOLoop.instance(),
                 keep_alive_timeout: int = DEFAULT_KEEPALIVE_TIMEOUT_MILLIS,
                 connect_timeout: int = DEFAULT_CONNECT_TIMEOUT_SEC,
                 request_timeout: int = DEFAULT_REQUEST_TIMEOUT_SEC):
        super().__init__(symbol, journal, loop, keep_alive_timeout, connect_timeout, request_timeout)

    def _get_url(self):
        return 'wss://ws-feed.pro.coinbase.com'

    def _create_subscribe_msg(self):
        return {
            'type': 'subscribe',
            'product_ids': [self.symbol],
            'channels': ['matches', 'heartbeat']
        }

    def _on_message_json(self, msg):
        if msg['type'] == 'match':
            self.appender.write_double(datetime.datetime.utcnow().timestamp())
            self.appender.write_long(msg['sequence'])
            self.appender.write_long(msg['trade_id'])
            self.appender.write_string(msg['product_id'])
            self.appender.write_short(1 if msg['side'] == 'buy' else 0)
            self.appender.write_double(float(msg['size']))
            self.appender.write_double(float(msg['price']))


def subscribe_coinbase_trades(journal_path: str = '/behemoth/journals/COINBASE_PRO_TRADES/BTC-USD'):
    logger = logging.getLogger(__name__)

    journal = Journal(Path(journal_path))
    subscriber = CoinbaseProSubscriber('BTC-USD', journal)

    logger.info("journaling ticks to {}".format(journal_path))

    IOLoop.instance().run_sync(subscriber.connect)
    IOLoop.instance().start()


if __name__ == '__main__':
    init_logging()
    fire.Fire(subscribe_coinbase_trades)

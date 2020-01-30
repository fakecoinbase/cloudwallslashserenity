import datetime
import fire
import logging

from cloudwall.serenity.mdrecorder.journal import Journal
from cloudwall.serenity.mdrecorder.subscriber import DEFAULT_KEEPALIVE_TIMEOUT_MILLIS, DEFAULT_CONNECT_TIMEOUT_SEC, \
    DEFAULT_REQUEST_TIMEOUT_SEC, WebsocketSubscriber
from cloudwall.serenity.mdrecorder.utils import init_logging
from pathlib import Path
from tornado.ioloop import IOLoop


class PhemexSubscriber(WebsocketSubscriber):

    def __init__(self, symbol: str, journal: Journal, loop: IOLoop = IOLoop.instance(),
                 keep_alive_timeout: int = DEFAULT_KEEPALIVE_TIMEOUT_MILLIS,
                 connect_timeout: int = DEFAULT_CONNECT_TIMEOUT_SEC,
                 request_timeout: int = DEFAULT_REQUEST_TIMEOUT_SEC):
        super().__init__(symbol, journal, loop, keep_alive_timeout, connect_timeout, request_timeout)

    def _get_url(self):
        return 'wss://phemex.com/ws'

    def _create_subscribe_msg(self):
        return {
            'id': 1,
            'method': 'trade.subscribe',
            'params': [self.symbol]
        }

    def _on_message_json(self, msg):
        if 'type' in msg and msg['type'] == 'incremental':
            for trade in msg["trades"]:
                self.appender.write_double(datetime.datetime.utcnow().timestamp())
                self.appender.write_long(msg['sequence'])
                self.appender.write_long(msg['sequence'])
                self.appender.write_string(msg['symbol'])
                self.appender.write_short(1 if trade[1] == 'bid' else 0)
                self.appender.write_double(float(trade[3]))
                self.appender.write_double(float(trade[2]))


def subscribe_phemex_trades(journal_path: str = '/behemoth/journals/PHEMEX_TRADES/BTCUSD'):
    logger = logging.getLogger(__name__)

    journal = Journal(Path(journal_path))
    subscriber = PhemexSubscriber('BTCUSD', journal)

    logger.info("journaling ticks to {}".format(journal_path))

    IOLoop.instance().run_sync(subscriber.connect)
    IOLoop.instance().start()


if __name__ == '__main__':
    init_logging()
    fire.Fire(subscribe_phemex_trades)

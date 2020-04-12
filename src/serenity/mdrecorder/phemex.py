import asyncio
import datetime
import json

import fire
import logging

from tau.core import MutableSignal, NetworkScheduler
from tau.event import Do
from tau.signal import Map, Filter

from serenity.mdrecorder.journal import Journal
from serenity.mdrecorder.subscriber import subscribe_trades
from serenity.mdrecorder.utils import init_logging
from pathlib import Path


def on_message_json(msg, appender):
    for trade in msg["trades"]:
        appender.write_double(datetime.datetime.utcnow().timestamp())
        appender.write_long(msg['sequence'])
        appender.write_long(msg['sequence'])
        appender.write_string(msg['symbol'])
        appender.write_short(1 if trade[1] == 'bid' else 0)
        appender.write_double(float(trade[3]))
        appender.write_double(float(trade[2]))


def subscribe_phemex_trades(journal_path: str = '/behemoth/journals/PHEMEX_TRADES/BTCUSD'):
    logger = logging.getLogger(__name__)

    journal = Journal(Path(journal_path))
    appender = journal.create_appender()
    logger.info("journaling ticks to {}".format(journal_path))

    uri = 'wss://phemex.com/ws'
    subscribe_msg = {
            'id': 1,
            'method': 'trade.subscribe',
            'params': ['BTCUSD']
    }

    messages = MutableSignal()
    scheduler = NetworkScheduler()
    network = scheduler.get_network()

    json_messages = Map(network, messages, lambda x: json.loads(x))
    incr_messages = Filter(network, json_messages,
                           lambda x: x.get('type', None) == 'incremental')
    Do(scheduler.get_network(), incr_messages, lambda: on_message_json(incr_messages.get_value(), appender))

    asyncio.get_event_loop().run_until_complete(subscribe_trades(uri, subscribe_msg, messages, scheduler))


if __name__ == '__main__':
    init_logging()
    fire.Fire(subscribe_phemex_trades)

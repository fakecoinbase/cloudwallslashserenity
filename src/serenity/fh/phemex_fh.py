import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import fire
import websockets
from phemex import PhemexConnection
from tau.core import Signal, MutableSignal, NetworkScheduler, Event
from tau.event import Do
from tau.signal import Map, Filter

from serenity.db import connect_serenity_db, TypeCodeCache, InstrumentCache
from serenity.fh.feedhandler import FeedHandler, Feed, FeedHandlerRegistry, FeedState
from serenity.model.exchange import ExchangeInstrument
from serenity.model.marketdata import Trade
from serenity.model.order import Side
from serenity.tickstore.journal import Journal
from serenity.utils import init_logging, FlatMap, custom_asyncio_error_handler


class PhemexFeed(Feed):
    logger = logging.getLogger(__name__)

    def __init__(self, scheduler: NetworkScheduler, type_code_cache: TypeCodeCache,
                 ws_uri: str, exch_instrument: ExchangeInstrument, price_scale: int):
        self.scheduler = scheduler
        self.type_code_cache = type_code_cache
        self.ws_uri = ws_uri
        self.instrument = exch_instrument
        self.price_scale = price_scale

        self.buy_code = type_code_cache.get_by_code(Side, 'Buy')
        self.sell_code = type_code_cache.get_by_code(Side, 'Sell')

        self.trades = None
        self.quotes = None

        self.feed_state = MutableSignal(FeedState.INIT)

    def get_instrument(self) -> ExchangeInstrument:
        return self.instrument

    def get_trades(self) -> Signal:
        return self.trades

    def get_quotes(self) -> Signal:
        raise NotImplementedError()

    def get_feed_state(self) -> Signal:
        return self.feed_state

    async def start(self):
        self.scheduler.schedule_update(self.feed_state, FeedState.STARTING)
        await self._subscribe_trades_and_quotes()

    async def _subscribe_trades_and_quotes(self):
        subscribe_msg = {
            'id': 1,
            'method': 'trade.subscribe',
            'params': [f'{self.instrument.get_exchange_instrument_code()}']
        }

        network = self.scheduler.get_network()

        messages = MutableSignal()
        json_messages = Map(network, messages, lambda x: json.loads(x))
        incr_messages = Filter(network, json_messages,
                               lambda x: x.get('type', None) == 'incremental')
        trade_lists = Map(network, incr_messages, lambda x: self._extract_trades(x))
        self.trades = FlatMap(self.scheduler, trade_lists).get_output()

        # self.trades is now valid, transition into LIVE state
        self.scheduler.schedule_update(self.feed_state, FeedState.LIVE)

        async with websockets.connect(self.ws_uri) as sock:
            await sock.send(json.dumps(subscribe_msg))
            while True:
                self.scheduler.schedule_update(messages, await sock.recv())

    def _extract_trades(self, msg) -> List[Trade]:
        trade_list = []
        for trade in msg['trades']:
            trade_id = trade[0]
            if trade[1] == 'Buy':
                side = self.buy_code
            else:
                side = self.sell_code
            price = float(trade[2]) / pow(10, self.price_scale)
            qty = float(trade[3])
            trade_list.append(Trade(self.get_instrument(), trade_id, side, qty, price))

        return trade_list


class PhemexFeedHandler(FeedHandler):
    logger = logging.getLogger(__name__)

    def __init__(self, scheduler: NetworkScheduler, instrument_cache: InstrumentCache,
                 instance_id: str = 'prod'):
        self.scheduler = scheduler
        self.instrument_cache = instrument_cache
        self.instance_id = instance_id
        if instance_id == 'prod':
            self.ws_uri = 'wss://phemex.com/ws'
            self.phemex = PhemexConnection()
        elif instance_id == 'test':
            self.ws_uri = 'wss://testnet.phemex.com/ws'
            self.phemex = PhemexConnection(api_url='https://testnet-api.phemex.com')
        else:
            raise ValueError(f'Unknown instance_id: {instance_id}')

        self.instruments = []
        self.known_instrument_ids = {}
        self.price_scaling = {}
        self._load_instruments()

    def get_uri_scheme(self) -> str:
        return 'phemex'

    def get_instance_id(self) -> str:
        return self.instance_id

    def get_instruments(self) -> List[ExchangeInstrument]:
        return self.instruments

    def get_feed(self, uri: str) -> Feed:
        (scheme, instance_id, instrument_id) = uri.split(':')
        if scheme != self.get_uri_scheme():
            raise ValueError(f'Unsupported URI scheme: {scheme}')
        if instance_id != self.get_instance_id():
            raise ValueError(f'Unsupported instance ID: {instance_id}')
        if instrument_id not in self.known_instrument_ids:
            raise ValueError(f'Unknown exchange Instrument: {instrument_id}')
        self.logger.info(f'Acquiring Feed for {uri}')

        return PhemexFeed(self.scheduler, self.instrument_cache.get_type_code_cache(), self.ws_uri,
                          self.known_instrument_ids[instrument_id], self.price_scaling[instrument_id])

    def _load_instruments(self):
        self.logger.info("Downloading supported products")
        products = self.phemex.get_products()
        for product in products['data']:
            symbol = product['symbol']
            base_ccy = product['baseCurrency']
            quote_ccy = product['quoteCurrency']
            price_scale = product['priceScale']

            ccy_pair = self.instrument_cache.get_or_create_currency_pair(base_ccy, quote_ccy)
            instr = ccy_pair.get_instrument()
            exch_instrument = self.instrument_cache.get_or_create_exchange_instrument(symbol, instr, "Phemex")
            self.logger.info(f'\t{symbol} - {base_ccy}/{quote_ccy} [ID #{instr.get_instrument_id()}]')
            self.known_instrument_ids[symbol] = exch_instrument
            self.instruments.append(exch_instrument)
            self.price_scaling[symbol] = price_scale


def main(instance_id: str = 'prod', journal_path: str = '/behemoth/journals/'):
    init_logging()
    logger = logging.getLogger(__name__)

    conn = connect_serenity_db()
    conn.autocommit = True
    cur = conn.cursor()

    instr_cache = InstrumentCache(cur, TypeCodeCache(cur))

    scheduler = NetworkScheduler()
    registry = FeedHandlerRegistry()
    fh = PhemexFeedHandler(scheduler, instr_cache)
    registry.register(fh)

    for instrument in fh.get_instruments():
        feed = registry.get_feed(f'phemex:{instance_id}:{instrument.get_exchange_instrument_code()}')

        # subscribe to FeedState in advance so we know when the Feed is ready to subscribe trades
        class SubscribeTrades(Event):
            def __init__(self, trade_feed: Feed):
                self.trade_feed = trade_feed
                instrument_code = trade_feed.get_instrument().get_exchange_instrument_code()
                self.journal = Journal(Path(f'{journal_path}/PHEMEX_TRADES/{instrument_code}'))
                self.appender = self.journal.create_appender()

            def on_activate(self) -> bool:
                if self.trade_feed.get_feed_state().get_value() == FeedState.LIVE:
                    trades = self.trade_feed.get_trades()
                    Do(scheduler.get_network(), trades, lambda: self.on_subscribe(trades.get_value()))
                return False

            def on_subscribe(self, trade):
                logger.info(trade)

                self.appender.write_double(datetime.utcnow().timestamp())
                self.appender.write_long(trade.get_trade_id())
                self.appender.write_long(trade.get_trade_id())
                self.appender.write_string(trade.get_instrument().get_exchange_instrument_code())
                self.appender.write_short(1 if trade.get_side().get_type_code() == 'Buy' else 0)
                self.appender.write_double(trade.get_qty())
                self.appender.write_double(trade.get_price())

        scheduler.get_network().connect(feed.get_feed_state(), SubscribeTrades(feed))

        # async start the feed
        asyncio.ensure_future(feed.start())

    # crash out on any exception
    asyncio.get_event_loop().set_exception_handler(custom_asyncio_error_handler)

    # go!
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    fire.Fire(main)

import json
import logging
from typing import List

import fire
import websockets
from phemex import PhemexConnection
from tau.core import MutableSignal, NetworkScheduler
from tau.signal import Map, Filter

from serenity.db import TypeCodeCache, InstrumentCache
from serenity.fh.feedhandler import FeedState, WebsocketFeedHandler, WebsocketFeed, \
    ws_fh_main
from serenity.model.exchange import ExchangeInstrument
from serenity.model.marketdata import Trade
from serenity.utils import FlatMap


class PhemexFeed(WebsocketFeed):
    def __init__(self, scheduler: NetworkScheduler, type_code_cache: TypeCodeCache, ws_uri: str,
                 exch_instrument: ExchangeInstrument, price_scale: int):
        super().__init__(scheduler, type_code_cache, ws_uri, exch_instrument)
        self.price_scale = price_scale

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


class PhemexFeedHandler(WebsocketFeedHandler):
    logger = logging.getLogger(__name__)

    def __init__(self, scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id: str = 'prod'):
        if instance_id == 'prod':
            self.ws_uri = 'wss://phemex.com/ws'
            self.phemex = PhemexConnection()
        elif instance_id == 'test':
            self.ws_uri = 'wss://testnet.phemex.com/ws'
            self.phemex = PhemexConnection(api_url='https://testnet-api.phemex.com')
        else:
            raise ValueError(f'Unknown instance_id: {instance_id}')

        # ensure we've initialized PhemexConnection before loading instruments in super()
        super().__init__(scheduler, instrument_cache, instance_id)

    @staticmethod
    def get_uri_scheme() -> str:
        return 'phemex'

    def _create_feed(self, scheduler, type_code_cache: TypeCodeCache, instrument: ExchangeInstrument):
        price_scale = self.price_scaling[instrument.get_exchange_instrument_code()]
        return PhemexFeed(scheduler, type_code_cache, self.ws_uri, instrument, price_scale)

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


def create_fh(scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id):
    return PhemexFeedHandler(scheduler, instrument_cache, instance_id)


def main(instance_id: str = 'prod', journal_path: str = '/behemoth/journals/'):
    ws_fh_main(create_fh, 'phemex', instance_id, journal_path, 'PHEMEX_TRADES')


if __name__ == '__main__':
    fire.Fire(main)

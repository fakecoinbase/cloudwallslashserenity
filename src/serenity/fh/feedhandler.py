import logging
from abc import ABC, abstractmethod
from typing import List

from tau.core import Signal

from serenity.model.instrument import Instrument


class Feed(ABC):
    """
    A marketdata feed with ability to subscribe to trades, quotes, etc..
    """
    @abstractmethod
    def get_instrument(self) -> Instrument:
        """
        Gets the trading instrument for which we are feeding data.
        """
        pass

    @abstractmethod
    def get_trades(self) -> Signal:
        """
        Gets all trade prints for this instrument on the connected exchange.
        """
        pass

    @abstractmethod
    def get_quotes(self) -> Signal:
        """
        Gets the top-of-book quote for this instrument on the connected exchange.
        """


class FeedHandler(ABC):
    """
    A connector for exchange marketdata.
    """

    @abstractmethod
    def get_uri_scheme(self) -> str:
        """
        Gets the short string name like 'phemex' or 'kraken' for this feedhandler.
        """
        pass

    @abstractmethod
    def get_instance_id(self) -> str:
        """
        Gets the specific instance connected to, e.g. 'prod' or 'test'
        """
        pass

    @abstractmethod
    def get_instruments(self) -> List[Instrument]:
        """
        Gets the instruments supported by this feedhandler.
        """
        pass

    @abstractmethod
    def get_feed(self, uri: str) -> Feed:
        """
        Acquires a feed for the given URI of the form scheme:instance:instrument_id, e.g.
        phemex:prod:BTCUSD or coinbase:test:BTC-USD. Raises an exception if the scheme:instance
        portion does not match this FeedHandler.
        """
        pass


class FeedHandlerRegistry:
    """
    A central registry of all known FeedHandlers.
    """

    logger = logging.getLogger(__name__)

    def __init__(self):
        self.fh_registry = {}

    def get_feed(self, uri: str) -> Feed:
        """
        Acquires a Feed for a FeedHandler based on a URI of the form scheme:instrument:instrument_id,
        e.g. phemex:prod:BTCUSD or coinbase:test:BTC-USD. Raises an exception if there is no
        registered handler for the given URI.
        """
        (scheme, instance, instrument_id) = uri.split(':')
        fh = self.fh_registry[f'{scheme}:{instance}']
        if not fh:
            raise ValueError(f'Unknown FeedHandler URI: {uri}')
        return fh.get_feed(uri)

    def register(self, feedhandler: FeedHandler):
        """
        Registers a FeedHandler so its feeds can be acquired centrally with get_feed().
        """
        fh_key = FeedHandlerRegistry._get_fh_key(feedhandler)
        self.fh_registry[fh_key] = feedhandler
        self.logger.info(f'registered FeedHandler: {fh_key}')

    @staticmethod
    def _get_fh_key(feedhandler: FeedHandler) -> str:
        return f'{feedhandler.get_uri_scheme()}:{feedhandler.get_instance_id()}'

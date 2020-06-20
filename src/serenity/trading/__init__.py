from abc import ABC, abstractmethod
from enum import Enum, auto
from uuid import uuid1

from tau.core import Signal

from serenity.model.instrument import Instrument


class Side(Enum):
    """
    Order side -- corresponds to long (buy) and short (sell) position.
    """
    BUY = auto()
    SELL = auto()


class TimeInForce(Enum):
    """
    Enumeration of supported TIF (time-in-force) values for the exchange.
    """
    DAY = auto()
    GTC = auto()
    IOC = auto()
    FOK = auto()


class ExecInst(Enum):
    """
    Enumeration of possible execution instructions to attach to an Order.
    """
    PARTICIPATE_DONT_INITIATE = auto()
    DO_NOT_INCREASE = auto()


class Order:
    """
    Base type for standard order types (limit and market).
    """
    @abstractmethod
    def __init__(self, qty: float, instrument: Instrument, side: Side):
        self.qty = qty
        self.instrument = instrument
        self.side = side

        self.cl_ord_id = str(uuid1())
        self.exec_inst = None

    def get_cl_ord_id(self) -> str:
        return self.cl_ord_id

    def get_qty(self) -> float:
        return self.qty

    def get_instrument(self) -> Instrument:
        return self.instrument

    def get_side(self) -> Side:
        return self.side

    def get_exec_inst(self) -> ExecInst:
        return self.exec_inst

    def set_exec_inst(self, exec_inst: ExecInst):
        self.exec_inst = exec_inst

    def get_order_parameter(self, name: str) -> object:
        pass

    def set_order_paramter(self, name: str, value: object):
        pass


class LimitOrder(Order):
    """
    An order with a maximum (buy) or minimum (sell) price to trade.
    """
    def __init__(self, price: float, qty: int, instrument: Instrument, side: Side,
                 time_in_force: TimeInForce = TimeInForce.GTC):
        super().__init__(qty, instrument, side)
        self.price = price
        self.time_in_force = time_in_force

    def get_price(self) -> float:
        return self.price

    def get_time_in_force(self) -> TimeInForce:
        return self.time_in_force


class MarketOrder(Order):
    """
    An order that executes at the prevailing market price.
    """
    def __init__(self, qty: int, instrument: Instrument, side: Side):
        super().__init__(qty, instrument, side)


class OrderFactory:
    """
    Helper factory for creating instances of different order types.
    """

    @staticmethod
    def create_market_order(side: Side, qty: int, instrument: Instrument) -> MarketOrder:
        return MarketOrder(qty, instrument, side)

    @staticmethod
    def create_limit_order(side: Side, qty: int, price: float, instrument: Instrument,
                           time_in_force: TimeInForce = TimeInForce.GTC) -> LimitOrder:
        return LimitOrder(price, qty, instrument, side, time_in_force)


class OrderPlacer(ABC):
    """
    Abstraction for the trading connection to the exchange.
    """

    def __init__(self, order_factory: OrderFactory):
        self.order_factory = order_factory

    @abstractmethod
    def get_order_events(self) -> Signal:
        pass

    def get_order_factory(self) -> OrderFactory:
        """"
        :return: the associated order factory object for this OrderPlacer
        """
        return self.order_factory

    @abstractmethod
    def submit(self, order: Order):
        """
        Places the given Order on the exchange
        :param order: order details
        """
        pass

    @abstractmethod
    def cancel(self, order: Order):
        """
        Cancels the referenced order.
        :param order: order to cancel
        """
        pass


class OrderPlacerService:
    def __init__(self):
        self.order_placers = {}

    def get_order_placer(self, uri: str) -> OrderPlacer:
        return self.order_placers.get(uri)

    def register_order_placer(self, uri: str, order_placer: OrderPlacer):
        self.order_placers[uri] = order_placer


class OrderEvent(ABC):
    pass


class ExecType:
    NEW = auto()
    DONE_FOR_DAY = auto()
    CANCELED = auto()
    REPLACE = auto()
    PENDING_CANCEL = auto()
    STOPPED = auto()
    REJECTED = auto()
    SUSPENDED = auto()
    PENDING_NEW = auto()
    CALCULATED = auto()
    EXPIRED = auto()
    RESTATED = auto()
    PENDING_REPLACE = auto()
    TRADE = auto()
    TRADE_CORRECT = auto()
    TRADE_CANCEL = auto()
    ORDER_STATUS = auto()


class OrderStatus:
    NEW = auto()
    PARTIALLY_FILLED = auto()
    FILLED = auto()
    DONE_FOR_DAY = auto()
    CANCELED = auto()
    PENDING_CANCEL = auto()
    STOPPED = auto()
    REJECTED = auto()
    SUSPENDED = auto()
    PENDING_NEW = auto()
    CALCULATED = auto()
    EXPIRED = auto()
    ACCEPTED_FOR_BIDDING = auto()
    PENDING_REPLACE = auto()


class ExecutionReport(OrderEvent):
    def __init__(self, order_id: str, cl_ord_id: str, exec_id: str, exec_type: ExecType,
                 order_status: OrderStatus, cum_qty: float, leaves_qty: float, last_px: float,
                 last_qty: float):
        self.order_id = order_id
        self.cl_ord_id = cl_ord_id
        self.exec_id = exec_id
        self.exec_type = exec_type
        self.order_status = order_status
        self.cum_qty = cum_qty
        self.leaves_qty = leaves_qty
        self.last_px = last_px
        self.last_qty = last_qty

    def get_order_id(self) -> str:
        return self.order_id

    def get_cl_ord_id(self) -> str:
        return self.cl_ord_id

    def get_exec_id(self) -> str:
        return self.exec_id

    def get_exec_type(self) -> ExecType:
        return self.exec_type

    def get_order_status(self) -> OrderStatus:
        return self.order_status

    def get_cum_qty(self) -> float:
        return self.cum_qty

    def get_leaves_qty(self) -> float:
        return self.leaves_qty

    def get_last_px(self) -> float:
        return self.last_px

    def get_last_qty(self) -> float:
        return self.last_qty


class Reject(OrderEvent):
    def __init__(self, message: str):
        self.message = message

    def get_message(self) -> str:
        return self.message


class CancelReject(OrderEvent):
    def __init__(self, cl_ord_id: str, orig_cl_ord_id: str, message: str):
        self.cl_ord_id = cl_ord_id
        self.orig_cl_ord_id = orig_cl_ord_id
        self.message = message

    def get_cl_ord_id(self) -> str:
        return self.cl_ord_id

    def get_orig_cl_ord_id(self) -> str:
        return self.orig_cl_ord_id

    def get_message(self) -> str:
        return self.message

from uuid import uuid1

from tau.core import Signal, NetworkScheduler, MutableSignal, Event

from serenity.marketdata import MarketdataService
from serenity.trading import OrderPlacer, Order, ExecutionReport, ExecType, OrderStatus, CancelReject, OrderFactory, \
    Side


class AutoFillOrderPlacer(OrderPlacer):
    def __init__(self, scheduler: NetworkScheduler, mds: MarketdataService):
        super().__init__(OrderFactory())
        self.scheduler = scheduler
        self.mds = mds

        self.order_events = MutableSignal()
        self.scheduler.get_network().attach(self.order_events)

        self.orders = {}

    def get_order_events(self) -> Signal:
        return self.order_events

    def submit(self, order: Order):
        order_id = str(uuid1())

        pending_new_rpt = ExecutionReport(order_id, order.get_cl_ord_id(), str(uuid1()), ExecType.PENDING_NEW,
                                          OrderStatus.PENDING_NEW, 0.0, order.get_qty(), 0.0, 0.0)
        self.scheduler.schedule_update(self.order_events, pending_new_rpt)

        new_rpt = ExecutionReport(order_id, order.get_cl_ord_id(), str(uuid1()), ExecType.NEW,
                                  OrderStatus.NEW, 0.0, order.get_qty(), 0.0, 0.0)
        self.scheduler.schedule_update(self.order_events, new_rpt)

        class FillScheduler(Event):
            def __init__(self, order_placer: AutoFillOrderPlacer, inner_order_books: Signal):
                self.order_placer = order_placer
                self.order_books = inner_order_books
                self.fired = False

            def on_activate(self) -> bool:
                if not self.fired:
                    if order.get_side() == Side.BUY:
                        fill_px = self.order_books.get_value().get_best_ask()
                    else:
                        fill_px = self.order_books.get_value().get_best_bid()
                    fill_rpt = ExecutionReport(order_id, order.get_cl_ord_id(), str(uuid1()), ExecType.TRADE,
                                               OrderStatus.FILLED, order.get_qty(), 0.0, fill_px, order.get_qty())
                    self.order_placer.scheduler.schedule_update(self.order_placer.order_events, fill_rpt)
                    self.fired = True
                return False

        order_books = self.mds.get_order_books(order.get_instrument())
        self.scheduler.get_network().connect(order_books, FillScheduler(self, order_books))

    def cancel(self, order):
        reject = CancelReject(order.get_cl_ord_id(), order.get_cl_ord_id(), 'Already fully filled')
        self.scheduler.schedule_update(self.order_events, reject)

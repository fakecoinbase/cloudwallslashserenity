from uuid import uuid1

from tau.core import Signal, NetworkScheduler, MutableSignal

from serenity.trading import OrderPlacer, Order, ExecutionReport, ExecType, OrderStatus, CancelReject, OrderFactory


class AutoFillOrderPlacer(OrderPlacer):
    def __init__(self, scheduler: NetworkScheduler):
        super().__init__(OrderFactory())
        self.scheduler = scheduler
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

        fill_rpt = ExecutionReport(order_id, order.get_cl_ord_id(), str(uuid1()), ExecType.NEW,
                                   OrderStatus.FILLED, order.get_qty(), 0.0, 0.0, order.get_qty())
        self.scheduler.schedule_update(self.order_events, fill_rpt)

    def cancel(self, order):
        reject = CancelReject(order.get_cl_ord_id(), order.get_cl_ord_id(), 'Already fully filled')
        self.scheduler.schedule_update(self.order_events, reject)

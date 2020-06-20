from tau.core import Signal

from serenity.trading import OrderPlacer, OrderHandle, Order


class PhemexOrderPlacer(OrderPlacer):
    def get_order_events(self) -> Signal:
        pass

    def submit(self, order: Order):
        pass

    def cancel(self, order: Order):
        pass

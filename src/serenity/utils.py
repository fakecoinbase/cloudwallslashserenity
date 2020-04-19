import logging

from tau.core import Signal, NetworkScheduler, MutableSignal


def init_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console_logger = logging.StreamHandler()
    console_logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_logger.setFormatter(formatter)
    logger.addHandler(console_logger)


def custom_asyncio_error_handler(loop, context):
    # first, handle with default handler
    loop.default_exception_handler(context)

    # force shutdown
    loop.stop()


class FlatMap(Signal):
    """
    Transforming function that applies a Callable to incoming values and updates the output value.

    .. seealso:: http://reactivex.io/documentation/operators/flatmap.html
    """
    def __init__(self, scheduler: NetworkScheduler, values: Signal):
        super().__init__()
        self.scheduler = scheduler
        self.values = values
        self.output = MutableSignal()
        scheduler.get_network().connect(values, self)
        scheduler.get_network().connect(self, self.output)

    def get_output(self):
        return self.output

    def on_activate(self):
        if self.values.is_valid():
            next_values = self.values.get_value()
            for next_value in next_values:
                self.scheduler.schedule_update(self.output, next_value)
            return True
        else:
            return False

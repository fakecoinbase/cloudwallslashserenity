import numpy as np

from tau.core import Network, Signal
from tau.signal import Function, WindowWithCount


class BollingerBands:
    def __init__(self, sma, upper, lower):
        self.sma = sma
        self.upper = upper
        self.lower = lower


class ComputeBollingerBands(Function):
    def __init__(self, network: Network, prices: Signal, window: int, num_std: int):
        super().__init__(network, [prices])
        self.prices = prices
        self.buffer = WindowWithCount(network, prices, window)
        self.num_std = num_std

    def _call(self):
        if self.buffer.is_valid():
            np_array = np.array(self.buffer.get_value())
            sma = np_array.mean()
            sd = np_array.std()
            upper = sma + (self.num_std * sd)
            lower = sma - (self.num_std * sd)
            self._update(BollingerBands(sma, upper, lower))

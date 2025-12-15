import time
import requests
import statistics
import logging
from collections import deque
from typing import Deque, List
import numpy as np
import matplotlib.pyplot as plt

# ================= CONFIG =================
BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"
SYMBOL = "BTCUSDT"

PRICE_WINDOW = 60           # ticks for return computation
VOL_WINDOW = 120            # volatility points shown
FETCH_INTERVAL = 1.0        # seconds
ANOMALY_Z = 2.5             # anomaly threshold

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ================= CORE ENGINE =================
class CryptoctopusEngine:
    def __init__(self):
        self.prices: Deque[float] = deque(maxlen=PRICE_WINDOW)
        self.volatility: Deque[float] = deque(maxlen=VOL_WINDOW)
        self.anomaly_flags: Deque[int] = deque(maxlen=VOL_WINDOW)

    def fetch_price(self) -> float:
        r = requests.get(BINANCE_URL, params={"symbol": SYMBOL}, timeout=2)
        r.raise_for_status()
        return float(r.json()["price"])

    def compute_returns(self) -> List[float]:
        return [
            (self.prices[i] - self.prices[i - 1]) / self.prices[i - 1]
            for i in range(1, len(self.prices))
        ]

    def compute_volatility(self, returns: List[float]) -> float:
        return statistics.stdev(returns) if len(returns) > 1 else 0.0

    def detect_anomaly(self, latest_return: float, volatility: float) -> bool:
        if volatility == 0:
            return False
        z_score = abs(latest_return) / volatility
        return z_score > ANOMALY_Z

    def process_tick(self, price: float):
        self.prices.append(price)

        if len(self.prices) < 2:
            return None

        returns = self.compute_returns()
        vol = self.compute_volatility(returns)
        latest_return = returns[-1]
        anomaly = self.detect_anomaly(latest_return, vol)

        self.volatility.append(vol)
        self.anomaly_flags.append(int(anomaly))

        logging.info(
            f"Price={price:.2f} | Vol={vol:.6f} | "
            f"Return={latest_return:+.5f} | "
            f"{'ANOMALY' if anomaly else 'OK'}"
        )

        return vol, anomaly

# ================= VISUALIZATION =================
class CryptoctopusVisualizer:
    def __init__(self):
        plt.ion()
        self.fig, (self.ax_price, self.ax_vol) = plt.subplots(2, 1, figsize=(10, 6))

        self.price_line, = self.ax_price.plot([], [], label="Price")
        self.vol_line, = self.ax_vol.plot([], [], label="Volatility")
        self.anomaly_scatter = self.ax_vol.scatter([], [], color="red", label="Anomaly")

        self.ax_price.set_title(f"{SYMBOL} Price")
        self.ax_vol.set_title("Rolling Volatility")

        self.ax_price.grid(True)
        self.ax_vol.grid(True)

        self.ax_vol.legend()

    def update(self, prices: Deque[float], vol: Deque[float], flags: Deque[int]):
        self.price_line.set_data(range(len(prices)), prices)
        self.vol_line.set_data(range(len(vol)), vol)

        anomaly_x = [i for i, f in enumerate(flags) if f == 1]
        anomaly_y = [vol[i] for i in anomaly_x]

        self.anomaly_scatter.remove()
        self.anomaly_scatter = self.ax_vol.scatter(
            anomaly_x, anomaly_y, color="red", s=30
        )

        self.ax_price.relim()
        self.ax_price.autoscale_view()

        self.ax_vol.relim()
        self.ax_vol.autoscale_view()

        plt.pause(0.01)

# ================= RUNNER =================
class CryptoctopusApp:
    def __init__(self):
        self.engine = CryptoctopusEngine()
        self.visualizer = CryptoctopusVisualizer()

    def run(self):
        logging.info("🐙 Cryptoctopus started (Elite Mode)")

        while True:
            try:
                price = self.engine.fetch_price()
                result = self.engine.process_tick(price)

                if result:
                    self.visualizer.update(
                        self.engine.prices,
                        self.engine.volatility,
                        self.engine.anomaly_flags
                    )

                time.sleep(FETCH_INTERVAL)

            except Exception as e:
                logging.error(f"Runtime error: {e}")
                time.sleep(2)

# ================= ENTRY =================
if __name__ == "__main__":
    CryptoctopusApp().run()

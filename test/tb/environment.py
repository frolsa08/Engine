"""Top-level assembly for agents, monitors, model, and scoreboard."""

from tb.clkrst_agent import ClkRstAgent, ClkRstMonitor
from tb.gpio_agent import GpioAgent, GpioMonitor
from tb.master_if_agent import MasterIfAgent, MasterIfMonitor
from tb.scoreboard import Scoreboard
from model.golden_model import PioGoldenModel


class VerificationEnvironment:
    def __init__(self, dut):
        self.clock_reset = ClkRstAgent(dut)
        self.clock_reset_monitor = ClkRstMonitor()
        self.master_if = MasterIfAgent(dut)
        self.master_if_monitor = MasterIfMonitor()
        self.gpio = GpioAgent(dut)
        self.gpio_monitor = GpioMonitor()
        self.scoreboard = Scoreboard(PioGoldenModel())

    async def start(self):
        """Start agents and monitors after their interfaces are defined."""
        raise NotImplementedError("Connect monitor publishers and start coroutines")
